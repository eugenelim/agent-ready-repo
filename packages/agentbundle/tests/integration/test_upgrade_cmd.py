"""T12: integration tests for ``agentbundle upgrade``.

Coverage:
  - Whole-pack upgrade: 0.1.0 → 0.2.0; installed-version updated; file content is 0.2.0.
  - Per-primitive upgrade (parametrised over all five flags): only matching files change.
  - Mixed-version surfacing: upgrade --skill first, then whole-pack → stderr has warning.
  - Primitive-not-found: --skill foo where foo not in pack → exit non-zero with message.
  - Hook-extension preservation: .sh stays .sh; .py stays .py after upgrade.
"""

from __future__ import annotations

import hashlib
import re
import shlex
import types
from pathlib import Path

import pytest

from tests._direct_acquisition import GitHttpsAcquisitionFake

# Fixture catalogue directories.
FIXTURE_ROOT = Path(__file__).parent.parent / "fixtures" / "upgrade"
CAT_V1 = FIXTURE_ROOT / "catalogue_v1"
CAT_V2 = FIXTURE_ROOT / "catalogue_v2"
CAT_V3 = FIXTURE_ROOT / "catalogue_v3"

PACK_V1 = CAT_V1 / "packs" / "core"
PACK_V2 = CAT_V2 / "packs" / "core"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _args_upgrade(
    pack: str,
    catalogue: str,
    root: str = ".",
    skill: str | None = None,
    agent: str | None = None,
    hook: str | None = None,
    seed: str | None = None,
    command: str | None = None,
    dry_run: bool = False,
    yes: bool = True,
) -> types.SimpleNamespace:
    # `yes=True` by default so non-prompt tests don't block on input(); the
    # confirmation-flow tests pass yes=False and monkeypatch input/isatty.
    return types.SimpleNamespace(
        pack=pack,
        catalogue=catalogue,
        root=root,
        skill=skill,
        agent=agent,
        hook=hook,
        seed=seed,
        command=command,
        dry_run=dry_run,
        yes=yes,
    )


def _args_install(pack: str, catalogue: str, output: str) -> types.SimpleNamespace:
    # Dist-tree fixtures need `emit_install_routes=True`.
    return types.SimpleNamespace(
        pack=pack,
        catalogue=catalogue,
        output=output,
        emit_install_routes=True,
    )


def _run_upgrade(**kwargs) -> int:
    from agentbundle.commands.upgrade import run

    return run(_args_upgrade(**kwargs))


def _run_install(pack: str, catalogue: str, output: str) -> int:
    from agentbundle.commands.install import run

    return run(_args_install(pack, catalogue, output))


def _install_v1(root: Path) -> int:
    """Helper: install core 0.1.0 into root."""
    return _run_install("core", str(CAT_V1), str(root))


def _write_direct_skill(source: Path, body: str = "# first\n") -> Path:
    skill = source / "skills" / "example"
    skill.mkdir(parents=True, exist_ok=True)
    (skill / "SKILL.md").write_text(
        "---\nname: example\n---\n" + body, encoding="utf-8"
    )
    return skill


def _write_capability_skill(
    source: Path,
    declarations: str,
    body: str = "# capability fixture\n",
) -> Path:
    """Write one direct skill with exact capability-frontmatter spelling."""

    skill = source / "skills" / "example"
    skill.mkdir(parents=True, exist_ok=True)
    capability_block = declarations.rstrip()
    if capability_block:
        capability_block += "\n"
    (skill / "SKILL.md").write_text(
        "---\nname: example\n" + capability_block + "---\n" + body,
        encoding="utf-8",
    )
    return skill


def _install_direct(
    source: Path | str,
    target: Path,
    *,
    scope: str = "repo",
    adapter: str = "claude-code",
) -> int:
    from agentbundle import cli

    return cli.main(
        [
            "install",
            str(source),
            "--skill",
            "example",
            "--scope",
            scope,
            "--adapter",
            adapter,
            "--output",
            str(target),
            "--yes",
        ]
    )


def _upgrade_direct(target: Path, *extra: str) -> int:
    from agentbundle import cli

    return cli.main(
        ["upgrade", "--skill", "example", "--root", str(target), *extra]
    )


def _tree_digests(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).digest()
        for path in root.rglob("*")
        if path.is_file()
    }


def _source_tree_digest(root: Path) -> str:
    """Derive the direct content digest without using lifecycle production code."""

    digest = hashlib.sha256()
    files = sorted(
        (path for path in root.rglob("*") if path.is_file()),
        key=lambda path: path.relative_to(root).as_posix().encode("utf-8"),
    )
    for path in files:
        relative = path.relative_to(root).as_posix().encode("utf-8")
        content = path.read_bytes()
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return f"sha256-1:{digest.hexdigest()}"


def _publisher_block_body(output: str) -> str:
    """Return the one fenced consent body after asserting its complete order."""

    from agentbundle.direct_install import (
        ADMISSIBILITY_VERDICT,
        PUBLISHER_BLOCK_CLOSE,
        PUBLISHER_BLOCK_OPEN,
    )

    lines = output.strip().splitlines()
    assert lines[0] == ADMISSIBILITY_VERDICT
    assert lines[-1] == ADMISSIBILITY_VERDICT
    assert lines.count(ADMISSIBILITY_VERDICT) == 2
    assert lines.count(PUBLISHER_BLOCK_OPEN) == 1
    assert lines.count(PUBLISHER_BLOCK_CLOSE) == 1
    open_index = lines.index(PUBLISHER_BLOCK_OPEN)
    close_index = lines.index(PUBLISHER_BLOCK_CLOSE)
    assert 0 < open_index < close_index < len(lines) - 1
    return "\n".join(lines[open_index + 1 : close_index])


def _run_printed_command(command: str) -> int:
    """Execute one rendered agentbundle command through the real CLI parser."""

    from agentbundle import cli

    argv = shlex.split(command)
    assert argv[0] == "agentbundle"
    return cli.main(argv[1:])


def _set_direct_source(target: Path, source: str | None) -> None:
    """Replace one fixture row's recorded source without changing its ownership."""

    from agentbundle.config import dump_state, load_state

    state_path = target / ".agentbundle-state.toml"
    state = load_state(state_path)
    row = state.row("example", "claude-code")
    assert row is not None
    row.source = source
    state_path.write_text(dump_state(state), encoding="utf-8", newline="\n")


def _set_direct_source_digest(target: Path, digest: str) -> None:
    """Replace the fixture row's digest while preserving every other field."""

    from agentbundle.config import dump_state, load_state

    state_path = target / ".agentbundle-state.toml"
    state = load_state(state_path)
    row = state.row("example", "claude-code")
    assert row is not None
    row.source_digest = digest
    state_path.write_text(dump_state(state), encoding="utf-8", newline="\n")


def _set_recorded_file_sha(target: Path, relpath: str, sha: str) -> None:
    """Replace one fixture row's recorded per-file integrity digest."""

    from agentbundle.config import dump_state, load_state

    state_path = target / ".agentbundle-state.toml"
    state = load_state(state_path)
    row = state.row("example", "claude-code")
    assert row is not None
    row.files[relpath]["sha"] = sha
    state_path.write_text(dump_state(state), encoding="utf-8", newline="\n")


def test_direct_skill_requires_matching_installed_row(tmp_path, capsys):
    assert _upgrade_direct(tmp_path) == 1
    captured = capsys.readouterr()
    assert "CAT-D023" in captured.err
    assert "is not installed at repo or user scope" in captured.err
    assert _tree_digests(tmp_path) == {}


def test_direct_skill_scope_ambiguity_names_scope_flag(tmp_path, capsys):
    source = tmp_path / "source"
    target = tmp_path / "target"
    _write_direct_skill(source)
    assert _install_direct(source, target) == 0
    assert _install_direct(source, target, scope="user") == 0
    capsys.readouterr()
    target_before = _tree_digests(target)
    user_root = Path.home()
    user_before = _tree_digests(user_root)

    assert _upgrade_direct(target) == 1
    refusal = capsys.readouterr()
    assert "CAT-D024" in refusal.err
    assert "--scope repo" in refusal.err
    assert _tree_digests(target) == target_before
    assert _tree_digests(user_root) == user_before
    assert _upgrade_direct(target, "--scope", "repo") == 0


def test_direct_skill_adapter_ambiguity_names_adapter_flag(tmp_path, capsys):
    source = tmp_path / "source"
    target = tmp_path / "target"
    _write_direct_skill(source)
    for adapter in ("claude-code", "codex", "kiro"):
        assert _install_direct(source, target, adapter=adapter) == 0
    capsys.readouterr()
    before = _tree_digests(target)

    assert _upgrade_direct(target) == 1
    refusal = capsys.readouterr()
    assert "CAT-D025" in refusal.err
    assert "--adapter codex" in refusal.err
    assert _tree_digests(target) == before
    assert _upgrade_direct(target, "--adapter", "codex") == 0


def _write_state_kind(
    target: Path,
    source_kind: str | None,
    *,
    adapters: tuple[str, ...] = ("claude-code",),
) -> None:
    from agentbundle.config import PackState, State, dump_state

    target.mkdir(parents=True, exist_ok=True)
    state = State(
        packs={
            ("example", adapter): PackState(
                installed_version="0.0.0+agentbundle.manifestless",
                source="/publisher/example",
                source_kind=source_kind,
                source_path="skills/example" if source_kind == "skill" else None,
                source_digest="sha256-1:" + "0" * 64,
                adapter=adapter,
            )
            for adapter in adapters
        }
    )
    (target / ".agentbundle-state.toml").write_text(dump_state(state))


def test_direct_skill_refuses_direct_pack_row_without_command(tmp_path, capsys):
    _write_state_kind(tmp_path, "pack")
    before = _tree_digests(tmp_path)
    assert _upgrade_direct(tmp_path) == 1
    refusal = capsys.readouterr()
    assert "CAT-D023" in refusal.err
    assert "directly installed pack" in refusal.err
    assert "agentbundle " not in refusal.err
    assert _tree_digests(tmp_path) == before


def test_direct_skill_refuses_catalogue_row_without_command(tmp_path, capsys):
    _write_state_kind(tmp_path, None)
    before = _tree_digests(tmp_path)
    assert _upgrade_direct(tmp_path) == 1
    refusal = capsys.readouterr()
    assert "CAT-D023" in refusal.err
    assert "catalogue pack" in refusal.err
    assert "agentbundle " not in refusal.err
    assert _tree_digests(tmp_path) == before


def test_pack_selector_refuses_direct_row_before_catalogue_and_recovery_executes(
    tmp_path, monkeypatch, capsys
):
    from agentbundle import cli
    from agentbundle.commands import upgrade

    source = tmp_path / "source"
    target = tmp_path / "target"
    _write_direct_skill(source)
    assert _install_direct(source, target) == 0
    capsys.readouterr()

    def _catalogue_must_not_resolve(*_args, **_kwargs):
        raise AssertionError("a direct row must refuse before catalogue resolution")

    monkeypatch.setattr(upgrade, "resolve_catalogue", _catalogue_must_not_resolve)
    monkeypatch.setattr(
        upgrade, "resolve_catalogue_uri", _catalogue_must_not_resolve
    )
    assert cli.main(
        [
            "upgrade",
            "--pack",
            "example",
            "--root",
            str(target),
            "--scope",
            "repo",
        ]
    ) == 1
    refusal = capsys.readouterr()
    assert "CAT-D036" in refusal.err
    command = next(
        line
        for line in refusal.err.splitlines()
        if line.startswith("agentbundle ")
    )
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    assert _run_printed_command(command) == 0


def test_direct_skill_json_refusal_uses_route_wording(tmp_path, capsys):
    source = tmp_path / "source"
    target = tmp_path / "target"
    _write_direct_skill(source)
    assert _install_direct(source, target) == 0
    capsys.readouterr()
    before = _tree_digests(target)

    assert _upgrade_direct(target, "--format", "json") == 1
    refusal = capsys.readouterr()
    assert "CAT-D034" in refusal.err
    assert "not supported for standalone --skill" in refusal.err
    assert "not yet supported with --pack" not in refusal.err
    assert _tree_digests(target) == before


def test_pack_selector_classifies_multi_adapter_direct_rows_before_versions(
    tmp_path, monkeypatch, capsys
):
    from agentbundle import cli
    from agentbundle.direct_source import recovery_command

    source = tmp_path / "source"
    target = tmp_path / "target"
    _write_direct_skill(source)
    assert _install_direct(source, target, adapter="claude-code") == 0
    assert _install_direct(source, target, adapter="codex") == 0
    capsys.readouterr()

    assert cli.main(
        [
            "upgrade",
            "--pack",
            "example",
            "--root",
            str(target),
            "--scope",
            "repo",
        ]
    ) == 1
    refusal = capsys.readouterr()
    assert "CAT-D033" in refusal.err
    assert "claude-code (—)" in refusal.err
    assert "codex (—)" in refusal.err
    assert "0.0.0+agentbundle.manifestless" not in refusal.err
    command = recovery_command(
        "agentbundle",
        "upgrade",
        "--skill",
        "example",
        "--root",
        str(target),
        "--scope",
        "repo",
        "--adapter",
        "codex",
        "--yes",
    )
    assert command in refusal.err
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    assert _run_printed_command(command) == 0


def test_pack_selector_multi_adapter_direct_pack_has_no_upgrade_route(
    tmp_path, capsys
):
    from agentbundle import cli

    _write_state_kind(
        tmp_path,
        "pack",
        adapters=("claude-code", "codex"),
    )

    assert cli.main(
        [
            "upgrade",
            "--pack",
            "example",
            "--root",
            str(tmp_path),
            "--scope",
            "repo",
        ]
    ) == 1
    refusal = capsys.readouterr()
    assert "CAT-D033" in refusal.err
    assert "no direct pack upgrade route is built" in refusal.err
    assert "agentbundle " not in refusal.err


def test_direct_skill_upgrade_succeeds(
    tmp_path, tmp_path_factory, monkeypatch, capsys
):
    storage = tmp_path_factory.mktemp("direct-upgrade-acquisition")
    acquisition = GitHttpsAcquisitionFake(monkeypatch, storage)
    source_tree = tmp_path / "source"
    skill = _write_direct_skill(source_tree)
    source = "git+https://github.com/example/skills@release"
    acquisition.publish("example/skills", "release", source_tree)
    target = tmp_path / "target"
    assert _install_direct(source, target) == 0
    capsys.readouterr()
    state_path = target / ".agentbundle-state.toml"
    state_before = hashlib.sha256(state_path.read_bytes()).digest()

    (skill / "SKILL.md").write_text("---\nname: example\n---\n# second\n")
    acquisition.publish("example/skills", "release", source_tree)
    assert _upgrade_direct(target, "--yes") == 0
    assert (target / ".claude/skills/example/SKILL.md").read_text().endswith(
        "# second\n"
    )
    assert hashlib.sha256(state_path.read_bytes()).digest() != state_before


def test_direct_skill_upgrade_reanchors_a_relative_source_to_its_state_root(
    tmp_path, monkeypatch, capsys
):
    from agentbundle.config import load_state

    target = tmp_path / "installation-root"
    source = target / "vendor"
    skill = _write_direct_skill(source)
    assert _install_direct(source, target) == 0
    capsys.readouterr()
    installed = load_state(target / ".agentbundle-state.toml").row(
        "example", "claude-code"
    )
    assert installed is not None
    assert installed.source == "vendor"

    (skill / "SKILL.md").write_text(
        "---\nname: example\n---\n# second\n", encoding="utf-8"
    )
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)

    assert _upgrade_direct(target, "--yes") == 0
    assert (target / ".claude/skills/example/SKILL.md").read_text(
        encoding="utf-8"
    ).endswith("# second\n")
    updated = load_state(target / ".agentbundle-state.toml").row(
        "example", "claude-code"
    )
    assert updated is not None
    assert updated.source == "vendor"


def test_direct_skill_upgrade_preserves_a_valid_stored_remote_source(tmp_path):
    from agentbundle.commands.upgrade import (
        _DirectSkillSelection,
        _select_direct_upgrade_source,
    )
    from agentbundle.config import PackState

    stored = "git+https://github.com/Owner/Repo@Release"
    row = PackState(
        installed_version="0.0.0+agentbundle.manifestless",
        source=stored,
        source_kind="skill",
        source_path="skills/example",
        source_digest="sha256-1:" + "0" * 64,
    )
    selection = _DirectSkillSelection(
        "repo", tmp_path / ".agentbundle-state.toml", row
    )

    assert _select_direct_upgrade_source("example", selection, None) == (
        stored,
        False,
    )


@pytest.mark.parametrize(
    "stored_source",
    [
        None,
        "agent-ready-repo",
        "git+https://github.com/example/skills@main",
        "https://[",
    ],
    ids=("absent", "legacy-sentinel", "ungrammatical", "malformed-url"),
)
def test_direct_skill_upgrade_refuses_an_unusable_stored_source(
    tmp_path, capsys, stored_source
):
    source = tmp_path / "source"
    target = tmp_path / "target"
    _write_direct_skill(source)
    assert _install_direct(source, target) == 0
    capsys.readouterr()
    _set_direct_source(target, stored_source)
    before = _tree_digests(target)

    assert _upgrade_direct(target, "--yes") == 1
    refusal = capsys.readouterr()
    assert "CAT-D030" in refusal.err
    named_placeholders = re.findall(
        r"source token (__AGENTBUNDLE_SOURCE(?:_[0-9]+)?__)", refusal.err
    )
    assert len(set(named_placeholders)) == 1
    assert _tree_digests(target) == before


def test_remote_consent_refusal_precedes_unusable_stored_source(
    tmp_path, tmp_path_factory, monkeypatch, capsys
):
    storage = tmp_path_factory.mktemp("direct-upgrade-consent-before-source")
    acquisition = GitHttpsAcquisitionFake(monkeypatch, storage)
    source_tree = tmp_path / "source"
    _write_direct_skill(source_tree)
    source = "git+https://github.com/example/skills@release"
    acquisition.publish("example/skills", "release", source_tree)
    target = tmp_path / "target"
    assert _install_direct(source, target) == 0
    capsys.readouterr()
    _set_direct_source(target, "git+https://github.com/example/skills@main")

    assert _upgrade_direct(target) == 1
    refusal = capsys.readouterr()
    assert "CAT-D008" in refusal.err
    assert "CAT-D030" not in refusal.err


def test_direct_skill_upgrade_preserves_absolute_source_spelling(tmp_path, capsys):
    from agentbundle.config import load_state

    source = tmp_path / "source"
    target = tmp_path / "target"
    skill = _write_direct_skill(source)
    assert _install_direct(source, target) == 0
    capsys.readouterr()
    stored = f"{tmp_path}//source"
    _set_direct_source(target, stored)
    (skill / "SKILL.md").write_text(
        "---\nname: example\n---\n# second\n", encoding="utf-8"
    )

    assert _upgrade_direct(target, "--yes") == 0
    row = load_state(target / ".agentbundle-state.toml").row(
        "example", "claude-code"
    )
    assert row is not None
    assert row.source == stored


def test_direct_skill_upgrade_rechecks_relative_source_confinement(
    tmp_path, monkeypatch, capsys
):
    target = tmp_path / "installation-root"
    source = target / "vendor"
    _write_direct_skill(source)
    assert _install_direct(source, target) == 0
    capsys.readouterr()

    outside = tmp_path / "outside-source"
    _write_direct_skill(outside)
    linked_source = target / "linked-source"
    try:
        linked_source.symlink_to(outside, target_is_directory=True)
    except OSError as exc:
        pytest.skip(f"directory symlink unavailable: {exc}")
    _set_direct_source(target, "linked-source")
    before = _tree_digests(target)
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)

    assert _upgrade_direct(target, "--yes") == 1
    refusal = capsys.readouterr()
    assert "CAT-D030" in refusal.err
    assert _tree_digests(target) == before


def test_unusable_stored_source_remediation_reinstalls_from_supplied_source(
    tmp_path, monkeypatch, capsys
):
    from agentbundle.config import load_state

    original = tmp_path / "original"
    target = tmp_path / "__AGENTBUNDLE_SOURCE__ installation root"
    skill = _write_direct_skill(original)
    references = skill / "references"
    references.mkdir()
    (references / "obsolete.md").write_text("old\n", encoding="utf-8")
    assert _install_direct(original, target) == 0
    capsys.readouterr()
    _set_direct_source(target, None)
    projection = target / ".claude/skills/example/SKILL.md"
    projection.write_text("# adopter edit\n", encoding="utf-8")

    replacement = tmp_path / "publisher's replacement; source"
    _write_direct_skill(replacement, "# wanted\n")
    assert _upgrade_direct(target, "--yes") == 1
    refusal = capsys.readouterr()
    assert "CAT-D030" in refusal.err
    assert str(projection) in refusal.err
    assert "move and keep" in refusal.err
    recovery = next(
        line.split("Then run: ", 1)[1]
        for line in refusal.err.splitlines()
        if "Then run: " in line
    )
    uninstall_command, install_command = recovery.split(" then ", 1)
    named_placeholders = re.findall(
        r"source token (__AGENTBUNDLE_SOURCE(?:_[0-9]+)?__)", refusal.err
    )
    assert len(set(named_placeholders)) == 1
    placeholder = named_placeholders[0]
    assert placeholder != "__AGENTBUNDLE_SOURCE__"
    assert shlex.split(install_command)[2] == placeholder

    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    kept_edit = tmp_path / "kept adopter edit.md"
    kept_edit.write_bytes(projection.read_bytes())
    projection.unlink()
    assert _run_printed_command(uninstall_command) == 0
    filled_install_command = install_command.replace(
        placeholder, shlex.quote(str(replacement))
    )
    assert placeholder not in filled_install_command
    assert _run_printed_command(filled_install_command) == 0

    row = load_state(target / ".agentbundle-state.toml").row(
        "example", "claude-code"
    )
    assert row is not None
    assert row.source == str(replacement)
    assert (target / ".claude/skills/example/SKILL.md").read_text(
        encoding="utf-8"
    ).endswith("# wanted\n")
    assert kept_edit.read_text(encoding="utf-8") == "# adopter edit\n"
    assert not (
        target / ".claude/skills/example/references/obsolete.md"
    ).exists()


@pytest.mark.parametrize(
    ("installed_ref", "installed_revision", "wanted_ref", "wanted_revision"),
    [
        ("a" * 40, "a" * 40, "b" * 40, "b" * 40),
        ("aaaaaaa", "a" * 40, "bbbbbbb", "b" * 40),
        ("release-1", "1" * 40, "release-2", "2" * 40),
    ],
    ids=("sha", "abbreviated-sha", "ref"),
)
def test_direct_skill_source_override_moves_each_remote_ref_kind(
    tmp_path,
    tmp_path_factory,
    monkeypatch,
    capsys,
    installed_ref,
    installed_revision,
    wanted_ref,
    wanted_revision,
):
    from agentbundle.config import load_state

    storage = tmp_path_factory.mktemp(f"direct-source-override-{wanted_ref[:7]}")
    acquisition = GitHttpsAcquisitionFake(monkeypatch, storage)
    first_tree = tmp_path / "first"
    second_tree = tmp_path / "second"
    _write_direct_skill(first_tree)
    _write_direct_skill(second_tree, "# second\n")
    repository = "git+https://github.com/example/skills"
    installed_source = f"{repository}@{installed_ref}"
    wanted_source = f"{repository}@{wanted_ref}"
    acquisition.publish(
        "example/skills", installed_ref, first_tree, revision=installed_revision
    )
    acquisition.publish(
        "example/skills", wanted_ref, second_tree, revision=wanted_revision
    )
    target = tmp_path / "target"
    assert _install_direct(installed_source, target) == 0
    capsys.readouterr()

    assert _upgrade_direct(target, "--source", wanted_source, "--yes") == 0
    row = load_state(target / ".agentbundle-state.toml").row(
        "example", "claude-code"
    )
    assert row is not None
    assert row.source == wanted_source
    assert row.source_revision == wanted_revision
    assert (target / ".claude/skills/example/SKILL.md").read_text().endswith(
        "# second\n"
    )


def test_root_single_unusable_source_recovery_omits_skill_selector(
    tmp_path, monkeypatch, capsys
):
    from agentbundle import cli
    from agentbundle.config import load_state

    original = tmp_path / "original" / "example"
    original.mkdir(parents=True)
    (original / "SKILL.md").write_text(
        "---\nname: example\n---\n# old\n", encoding="utf-8"
    )
    target = tmp_path / "target"
    assert cli.main(
        [
            "install",
            str(original),
            "--scope",
            "repo",
            "--adapter",
            "claude-code",
            "--output",
            str(target),
            "--yes",
        ]
    ) == 0
    capsys.readouterr()
    _set_direct_source(target, None)

    replacement = tmp_path / "replacement" / "example"
    replacement.mkdir(parents=True)
    (replacement / "SKILL.md").write_text(
        "---\nname: example\n---\n# wanted\n", encoding="utf-8"
    )
    assert _upgrade_direct(target, "--yes") == 1
    refusal = capsys.readouterr()
    recovery = next(
        line.split("Then run: ", 1)[1]
        for line in refusal.err.splitlines()
        if "Then run: " in line
    )
    uninstall_command, install_command = recovery.split(" then ", 1)
    install_argv = shlex.split(install_command)
    assert "--skill" not in install_argv
    placeholder = install_argv[2]

    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    assert _run_printed_command(uninstall_command) == 0
    filled_install = install_command.replace(
        placeholder, shlex.quote(str(replacement))
    )
    assert _run_printed_command(filled_install) == 0
    row = load_state(target / ".agentbundle-state.toml").row(
        "example", "claude-code"
    )
    assert row is not None
    assert row.source_path == "."
    assert (target / ".claude/skills/example/SKILL.md").read_text(
        encoding="utf-8"
    ).endswith("# wanted\n")


def test_direct_skill_source_override_refuses_a_local_row(tmp_path, capsys):
    source = tmp_path / "source"
    target = tmp_path / "target"
    _write_direct_skill(source)
    assert _install_direct(source, target) == 0
    capsys.readouterr()
    before = _tree_digests(target)

    remote = "git+https://github.com/example/skills@release-2"
    assert _upgrade_direct(target, "--source", remote, "--yes") == 1
    refusal = capsys.readouterr()
    assert "CAT-D028" in refusal.err
    assert _tree_digests(target) == before


def test_direct_skill_source_override_refuses_a_different_repository(
    tmp_path, tmp_path_factory, monkeypatch, capsys
):
    storage = tmp_path_factory.mktemp("direct-source-other-repository")
    acquisition = GitHttpsAcquisitionFake(monkeypatch, storage)
    source_tree = tmp_path / "source"
    _write_direct_skill(source_tree)
    installed = "git+https://github.com/example/skills@release-1"
    supplied = "git+https://github.com/other/skills@release-2"
    acquisition.publish("example/skills", "release-1", source_tree)
    acquisition.publish("other/skills", "release-2", source_tree)
    target = tmp_path / "target"
    assert _install_direct(installed, target) == 0
    capsys.readouterr()
    acquisition.calls.clear()
    before = _tree_digests(target)

    assert _upgrade_direct(target, "--source", supplied, "--yes") == 1
    refusal = capsys.readouterr()
    assert "CAT-D029" in refusal.err
    assert acquisition.calls == []
    assert _tree_digests(target) == before


@pytest.mark.parametrize("edited_kind", ["incoming", "removal"])
def test_source_override_adopter_edit_retry_preserves_wanted_revision(
    tmp_path, tmp_path_factory, monkeypatch, capsys, edited_kind
):
    from agentbundle.config import load_state

    storage = tmp_path_factory.mktemp(f"direct-edit-retry-{edited_kind}")
    acquisition = GitHttpsAcquisitionFake(monkeypatch, storage)
    first_tree = tmp_path / "first"
    wanted_tree = tmp_path / "wanted"
    first_skill = _write_direct_skill(first_tree)
    wanted_skill = _write_direct_skill(wanted_tree, "# wanted\n")
    for skill in (first_skill, wanted_skill):
        references = skill / "references"
        references.mkdir()
        (references / "keep.md").write_text("keep\n", encoding="utf-8")
    (first_skill / "references" / "doomed.md").write_text(
        "publisher\n", encoding="utf-8"
    )

    repository = "git+https://github.com/example/skills"
    installed = f"{repository}@{'1' * 40}"
    wanted = f"{repository}@{'2' * 40}"
    acquisition.publish("example/skills", "1" * 40, first_tree, revision="1" * 40)
    acquisition.publish("example/skills", "2" * 40, wanted_tree, revision="2" * 40)
    target = tmp_path / "target"
    assert _install_direct(installed, target) == 0
    capsys.readouterr()

    projected_skill = target / ".claude/skills/example/SKILL.md"
    recorded_skill = projected_skill.read_bytes()
    edited_path = projected_skill
    if edited_kind == "removal":
        edited_path = target / ".claude/skills/example/references/doomed.md"
    edited_path.write_text("adopter edit\n", encoding="utf-8")

    assert _upgrade_direct(target, "--source", wanted, "--yes") == 1
    refusal = capsys.readouterr()
    assert "CAT-D027" in refusal.err
    retry = next(
        line.split("then run ", 1)[1].removesuffix(".")
        for line in refusal.err.splitlines()
        if "then run " in line
    )
    retry_argv = shlex.split(retry)
    assert retry_argv[retry_argv.index("--source") + 1] == wanted

    if edited_kind == "incoming":
        projected_skill.write_bytes(recorded_skill)
    else:
        edited_path.unlink()
    assert _run_printed_command(retry) == 0
    row = load_state(target / ".agentbundle-state.toml").row(
        "example", "claude-code"
    )
    assert row is not None
    assert row.source == wanted
    assert row.source_revision == "2" * 40
    assert projected_skill.read_text(encoding="utf-8").endswith("# wanted\n")
    assert not (target / ".claude/skills/example/references/doomed.md").exists()


def test_different_ref_install_remediation_executes_from_another_directory(
    tmp_path, tmp_path_factory, monkeypatch, capsys
):
    from agentbundle.config import load_state

    storage = tmp_path_factory.mktemp("direct-ref-remediation")
    acquisition = GitHttpsAcquisitionFake(monkeypatch, storage)
    first_tree = tmp_path / "first"
    second_tree = tmp_path / "second"
    _write_direct_skill(first_tree)
    _write_direct_skill(second_tree, "# wanted\n")
    first = "git+https://github.com/example/skills@release-1"
    wanted = "git+https://github.com/example/skills@release-2"
    acquisition.publish("example/skills", "release-1", first_tree, revision="1" * 40)
    acquisition.publish("example/skills", "release-2", second_tree, revision="2" * 40)
    target = tmp_path / "installation root"
    assert _install_direct(first, target) == 0
    capsys.readouterr()

    assert _install_direct(wanted, target) == 1
    refusal = capsys.readouterr()
    assert "CAT-D022" in refusal.err
    recovery_line = next(
        line for line in refusal.err.splitlines() if line.startswith("  → Run ")
    )
    suffix = " to move the installed skill to this ref."
    command = recovery_line.removeprefix("  → Run ").removesuffix(suffix)
    assert shlex.split(command) == [
        "agentbundle",
        "upgrade",
        "--skill",
        "example",
        "--source",
        wanted,
        "--root",
        str(target),
        "--scope",
        "repo",
        "--adapter",
        "claude-code",
        "--yes",
    ]
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)

    assert _run_printed_command(command) == 0
    row = load_state(target / ".agentbundle-state.toml").row(
        "example", "claude-code"
    )
    assert row is not None
    assert row.source == wanted
    assert row.source_revision == "2" * 40
    assert (target / ".claude/skills/example/SKILL.md").read_text().endswith(
        "# wanted\n"
    )


def test_direct_skill_upgrade_plans_writes_and_removals_without_catalogue(
    tmp_path, tmp_path_factory, monkeypatch, capsys
):
    from agentbundle.commands import upgrade
    from agentbundle.config import load_state

    storage = tmp_path_factory.mktemp("direct-upgrade-plan")
    acquisition = GitHttpsAcquisitionFake(monkeypatch, storage)
    source_tree = tmp_path / "source"
    skill = _write_direct_skill(source_tree)
    references = skill / "references"
    references.mkdir()
    obsolete = references / "obsolete.md"
    obsolete.write_text("old\n")
    source = "git+https://github.com/example/skills@release"
    acquisition.publish("example/skills", "release", source_tree)
    target = tmp_path / "target"
    assert _install_direct(source, target) == 0
    capsys.readouterr()

    (skill / "SKILL.md").write_text("---\nname: example\n---\n# second\n")
    obsolete.unlink()
    scripts = skill / "scripts"
    scripts.mkdir()
    (scripts / "added.py").write_text("print('new')\n")
    acquisition.publish("example/skills", "release", source_tree)
    before = _tree_digests(target)

    def _catalogue_must_not_resolve(*_args, **_kwargs):
        raise AssertionError("standalone skill upgrade must not resolve a catalogue")

    monkeypatch.setattr(upgrade, "resolve_catalogue", _catalogue_must_not_resolve)
    monkeypatch.setattr(
        upgrade, "resolve_catalogue_uri", _catalogue_must_not_resolve
    )
    assert _upgrade_direct(target, "--dry-run") == 0
    preview = capsys.readouterr()
    assert "write .claude/skills/example/SKILL.md" in preview.out
    assert "write .claude/skills/example/scripts/added.py" in preview.out
    assert "remove .claude/skills/example/references/obsolete.md" in preview.out
    assert _tree_digests(target) == before

    assert _upgrade_direct(target, "--yes") == 0
    applied = capsys.readouterr()
    assert "remove .claude/skills/example/references/obsolete.md" in applied.out
    assert (target / ".claude/skills/example/SKILL.md").read_text().endswith(
        "# second\n"
    )
    assert (target / ".claude/skills/example/scripts/added.py").read_text() == (
        "print('new')\n"
    )
    projected_obsolete = target / ".claude/skills/example/references/obsolete.md"
    assert not projected_obsolete.exists()
    assert not projected_obsolete.parent.exists()
    row = load_state(target / ".agentbundle-state.toml").row(
        "example", "claude-code"
    )
    assert row is not None
    assert ".claude/skills/example/references/obsolete.md" not in row.files
    assert ".claude/skills/example/scripts/added.py" in row.files


@pytest.mark.parametrize("dry_run", [False, True])
def test_direct_skill_upgrade_refuses_an_unsafe_destination_before_planning(
    tmp_path, capsys, dry_run
):
    source = tmp_path / "source"
    target = tmp_path / "target"
    skill = _write_direct_skill(source)
    references = skill / "references"
    references.mkdir()
    (references / "unsafe.md").write_text("# first\n")
    assert _install_direct(source, target) == 0
    capsys.readouterr()

    projected_skill = target / ".claude/skills/example/SKILL.md"
    unsafe_projection = target / ".claude/skills/example/references/unsafe.md"
    outside = tmp_path / "outside.md"
    outside.write_text("# adopter bytes\n")
    unsafe_projection.unlink()
    unsafe_projection.symlink_to(outside)
    (skill / "SKILL.md").write_text("---\nname: example\n---\n# second\n")
    (references / "unsafe.md").write_text("# second\n")
    before = _tree_digests(target)
    outside_before = hashlib.sha256(outside.read_bytes()).digest()

    flags = ("--dry-run",) if dry_run else ("--yes",)
    assert _upgrade_direct(target, *flags) == 1
    refusal = capsys.readouterr()
    assert "CAT-D009" in refusal.err
    assert ".claude/skills/example/references/unsafe.md" in refusal.err
    assert "upgrade plan" not in refusal.out
    assert _tree_digests(target) == before
    assert hashlib.sha256(outside.read_bytes()).digest() == outside_before
    assert unsafe_projection.is_symlink()
    assert projected_skill.read_text().endswith("# first\n")


@pytest.mark.parametrize("dry_run", [False, True])
def test_direct_skill_upgrade_refuses_an_edited_incoming_destination(
    tmp_path, capsys, dry_run
):
    source = tmp_path / "source"
    target = tmp_path / "target"
    skill = _write_direct_skill(source)
    assert _install_direct(source, target) == 0
    capsys.readouterr()
    projection = target / ".claude/skills/example/SKILL.md"
    projection.write_text("# adopter edit\n")
    (skill / "SKILL.md").write_text("---\nname: example\n---\n# second\n")
    before = _tree_digests(target)

    flags = ("--dry-run",) if dry_run else ("--yes",)
    assert _upgrade_direct(target, *flags) == 1
    refusal = capsys.readouterr()
    assert "CAT-D027" in refusal.err
    assert ".claude/skills/example/SKILL.md" in refusal.err
    assert "upgrade plan" not in refusal.out
    assert _tree_digests(target) == before


@pytest.mark.parametrize("dry_run", [False, True])
def test_direct_skill_upgrade_reapplies_admission_before_planning(
    tmp_path, monkeypatch, capsys, dry_run
):
    from agentbundle import direct_source

    source = tmp_path / "source"
    target = tmp_path / "target"
    skill = _write_direct_skill(source)
    assert _install_direct(source, target) == 0
    capsys.readouterr()
    (skill / "SKILL.md").write_text("---\nname: example\n---\n# second\n")
    before = _tree_digests(target)
    calls: list[Path] = []
    validate = direct_source.validate_direct_source

    def _observe(candidate: Path):
        calls.append(candidate)
        return validate(candidate)

    monkeypatch.setattr(direct_source, "validate_direct_source", _observe)

    flags = ("--dry-run",) if dry_run else ("--yes",)
    assert _upgrade_direct(target, *flags) == 0
    assert calls == [source]
    captured = capsys.readouterr()
    assert "upgrade plan" in captured.out
    if dry_run:
        assert _tree_digests(target) == before
    else:
        assert _tree_digests(target) != before


@pytest.mark.parametrize("dry_run", [False, True])
def test_direct_skill_upgrade_refuses_an_edited_removal_destination(
    tmp_path, capsys, dry_run
):
    source = tmp_path / "source"
    target = tmp_path / "target"
    skill = _write_direct_skill(source)
    references = skill / "references"
    references.mkdir()
    doomed = references / "doomed.md"
    doomed.write_text("publisher\n")
    assert _install_direct(source, target) == 0
    capsys.readouterr()
    projected_doomed = target / ".claude/skills/example/references/doomed.md"
    projected_doomed.write_text("adopter\n")
    doomed.unlink()
    (skill / "SKILL.md").write_text("---\nname: example\n---\n# second\n")
    before = _tree_digests(target)

    flags = ("--dry-run",) if dry_run else ("--yes",)
    assert _upgrade_direct(target, *flags) == 1
    refusal = capsys.readouterr()
    assert "CAT-D027" in refusal.err
    assert "doomed.md" in refusal.err
    assert "upgrade plan" not in refusal.out
    assert _tree_digests(target) == before


def test_direct_skill_upgrade_keeps_a_cross_scope_owned_removal(
    tmp_path, monkeypatch, capsys
):
    from agentbundle.config import load_state

    source = tmp_path / "source"
    target = tmp_path / "target"
    skill = _write_direct_skill(source)
    references = skill / "references"
    references.mkdir()
    doomed = references / "doomed.md"
    doomed.write_text("publisher\n")
    monkeypatch.setenv("HOME", str(target))
    monkeypatch.setenv("AGENTBUNDLE_USER_ROOT", str(target))
    assert _install_direct(source, target, scope="repo") == 0
    assert _install_direct(source, target, scope="user") == 0
    capsys.readouterr()
    repo_state_path = target / ".agentbundle-state.toml"
    user_state_path = target / ".agentbundle/state.toml"
    relpath = ".claude/skills/example/references/doomed.md"
    assert relpath in load_state(repo_state_path).row("example", "claude-code").files
    assert relpath in load_state(user_state_path).row("example", "claude-code").files
    projected = target / relpath
    doomed.unlink()
    (skill / "SKILL.md").write_text("---\nname: example\n---\n# second\n")

    assert _upgrade_direct(target, "--scope", "repo", "--yes") == 0
    repo_row = load_state(repo_state_path).row("example", "claude-code")
    user_row = load_state(user_state_path).row("example", "claude-code")
    assert repo_row is not None and user_row is not None
    assert projected.exists()
    assert relpath not in repo_row.files
    assert relpath in user_row.files


def test_direct_skill_upgrade_keeps_ownership_when_peer_state_is_unreadable(
    tmp_path, monkeypatch, capsys
):
    from agentbundle import config
    from agentbundle.config import ConfigError, load_state

    source = tmp_path / "source"
    target = tmp_path / "target"
    skill = _write_direct_skill(source)
    references = skill / "references"
    references.mkdir()
    doomed = references / "doomed.md"
    doomed.write_text("publisher\n")
    monkeypatch.setenv("HOME", str(target))
    monkeypatch.setenv("AGENTBUNDLE_USER_ROOT", str(target))
    assert _install_direct(source, target, scope="repo") == 0
    assert _install_direct(source, target, scope="user") == 0
    capsys.readouterr()
    repo_state_path = target / ".agentbundle-state.toml"
    peer_state_path = target / ".agentbundle/state.toml"
    relpath = ".claude/skills/example/references/doomed.md"
    projected = target / relpath
    doomed.unlink()
    (skill / "SKILL.md").write_text("---\nname: example\n---\n# second\n")
    real_load = config.load_state

    def _refuse_peer(path, *, for_write=False):
        if path == peer_state_path:
            raise ConfigError("peer state unreadable")
        return real_load(path, for_write=for_write)

    monkeypatch.setattr(config, "load_state", _refuse_peer)
    assert _upgrade_direct(target, "--scope", "repo", "--yes") == 0
    row = load_state(repo_state_path).row("example", "claude-code")
    assert row is not None
    assert projected.exists()
    assert relpath in row.files


def test_direct_skill_upgrade_unlink_failure_keeps_state_and_file(
    tmp_path, monkeypatch, capsys
):
    source = tmp_path / "source"
    target = tmp_path / "target"
    skill = _write_direct_skill(source)
    references = skill / "references"
    references.mkdir()
    doomed = references / "doomed.md"
    doomed.write_text("publisher\n")
    assert _install_direct(source, target) == 0
    capsys.readouterr()
    state_path = target / ".agentbundle-state.toml"
    before = state_path.read_bytes()
    projected = target / ".claude/skills/example/references/doomed.md"
    doomed.unlink()
    (skill / "SKILL.md").write_text("---\nname: example\n---\n# second\n")
    real_unlink = Path.unlink

    def _refuse_unlink(path, *args, **kwargs):
        if path == projected:
            raise PermissionError("fixture obstruction")
        return real_unlink(path, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", _refuse_unlink)
    assert _upgrade_direct(target, "--yes") == 1
    refusal = capsys.readouterr()
    assert "CAT-D020" in refusal.err
    assert "doomed.md" in refusal.err
    assert state_path.read_bytes() == before
    assert projected.exists()


def test_direct_skill_upgrade_prune_failure_keeps_state_and_empty_directory(
    tmp_path, monkeypatch, capsys
):
    from agentbundle.config import load_state

    source = tmp_path / "source"
    target = tmp_path / "target"
    skill = _write_direct_skill(source)
    references = skill / "references"
    references.mkdir()
    doomed = references / "doomed.md"
    doomed.write_text("publisher\n")
    assert _install_direct(source, target) == 0
    capsys.readouterr()
    state_path = target / ".agentbundle-state.toml"
    before = state_path.read_bytes()
    projected = target / ".claude/skills/example/references/doomed.md"
    projected_directory = projected.parent
    projected_skill = target / ".claude/skills/example/SKILL.md"
    projected_skill_before = projected_skill.read_bytes()
    doomed.unlink()
    (skill / "SKILL.md").write_text("---\nname: example\n---\n# second\n")
    real_rmdir = Path.rmdir

    def _refuse_rmdir(path):
        if path == projected_directory:
            raise PermissionError("fixture obstruction")
        return real_rmdir(path)

    with monkeypatch.context() as patcher:
        patcher.setattr(Path, "rmdir", _refuse_rmdir)
        assert _upgrade_direct(target, "--yes") == 1
    refusal = capsys.readouterr()
    assert "CAT-D021" in refusal.err
    assert "references" in refusal.err
    retry_command = next(
        line.split("then retry: ", 1)[1]
        for line in refusal.err.splitlines()
        if "then retry: " in line
    )
    assert state_path.read_bytes() == before
    assert not projected.exists()
    assert projected_directory.is_dir()
    assert list(projected_directory.iterdir()) == []
    assert projected_skill.read_bytes() == projected_skill_before

    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    assert _run_printed_command(retry_command) == 0
    capsys.readouterr()
    assert not projected_directory.exists()
    assert projected_skill.read_text().endswith("# second\n")
    row = load_state(state_path).row("example", "claude-code")
    assert row is not None
    assert ".claude/skills/example/references/doomed.md" not in row.files


@pytest.mark.parametrize("terminal", ["moved", "removed"])
def test_direct_skill_missing_source_path_remediation_reaches_terminal_state(
    tmp_path, tmp_path_factory, monkeypatch, capsys, terminal
):
    from agentbundle.config import load_state

    storage = tmp_path_factory.mktemp(f"direct-missing-path-{terminal}")
    acquisition = GitHttpsAcquisitionFake(monkeypatch, storage)
    original_source = tmp_path / "original-source"
    _write_direct_skill(original_source)
    other = original_source / "skills" / "other"
    other.mkdir()
    (other / "SKILL.md").write_text("---\nname: other\n---\n# other\n")
    source = "git+https://github.com/example/skills@release"
    acquisition.publish("example/skills", "release", original_source)
    target = tmp_path / "target"
    assert _install_direct(source, target) == 0
    capsys.readouterr()
    before = _tree_digests(target)

    updated_source = tmp_path / "updated-source"
    updated_other = updated_source / "skills" / "other"
    updated_other.mkdir(parents=True)
    (updated_other / "SKILL.md").write_text("---\nname: other\n---\n# other\n")
    if terminal == "moved":
        renamed = updated_source / "skills" / "renamed"
        renamed.mkdir()
        (renamed / "SKILL.md").write_text("---\nname: renamed\n---\n# moved\n")
    acquisition.publish("example/skills", "release", updated_source)

    assert _upgrade_direct(target, "--yes") == 1
    wet_refusal = capsys.readouterr()
    assert "CAT-D026" in wet_refusal.err
    assert "skills/example" in wet_refusal.err
    assert _tree_digests(target) == before

    assert _upgrade_direct(target, "--dry-run") == 1
    refusal = capsys.readouterr()
    assert "CAT-D026" in refusal.err
    assert "skills/example" in refusal.err
    assert _tree_digests(target) == before

    remediation = next(
        line.removeprefix("  → ")
        for line in refusal.err.splitlines()
        if line.startswith("  → moved: ")
    )
    moved_line, removed_line = remediation.removeprefix("moved: ").split(
        "; removed: ", 1
    )
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    if terminal == "moved":
        uninstall_command, install_command = moved_line.split(" then ", 1)
        assert _run_printed_command(uninstall_command) == 0
        assert _run_printed_command(
            install_command.replace("<new-source-path>", "renamed")
        ) == 0
        state = load_state(target / ".agentbundle-state.toml")
        assert state.row("renamed", "claude-code") is not None
        assert state.row("example", "claude-code") is None
        assert not (target / ".claude/skills/example/SKILL.md").exists()
    else:
        assert _run_printed_command(removed_line) == 0
        state = load_state(target / ".agentbundle-state.toml")
        assert state.row("example", "claude-code") is None
        assert not (target / ".claude/skills/example/SKILL.md").exists()


@pytest.mark.parametrize("terminal_attached", [False, True])
def test_remote_direct_skill_requires_yes_before_acquisition(
    tmp_path, tmp_path_factory, monkeypatch, capsys, terminal_attached
):
    from agentbundle.direct_install import (
        ADMISSIBILITY_VERDICT,
        PUBLISHER_BLOCK_CLOSE,
        PUBLISHER_BLOCK_OPEN,
    )

    storage = tmp_path_factory.mktemp("direct-upgrade-consent")
    acquisition = GitHttpsAcquisitionFake(monkeypatch, storage)
    source_tree = tmp_path / "source"
    _write_direct_skill(source_tree)
    source = "git+https://github.com/example/skills@release"
    acquisition.publish("example/skills", "release", source_tree)
    target = tmp_path / "target"
    assert _install_direct(source, target) == 0
    capsys.readouterr()
    acquisition.calls.clear()
    before = _tree_digests(target)
    monkeypatch.setattr("sys.stdin.isatty", lambda: terminal_attached)

    assert _upgrade_direct(target) == 1
    refusal = capsys.readouterr()
    combined = refusal.out + refusal.err
    assert refusal.out == ""
    assert refusal.err == (
        "upgrade: [CAT-D008] a remote standalone skill upgrade requires --yes "
        "before acquisition\n"
        "Re-run with --yes, or use --dry-run to preview without writing.\n"
    )
    assert acquisition.calls == []
    assert PUBLISHER_BLOCK_OPEN not in combined
    assert PUBLISHER_BLOCK_CLOSE not in combined
    assert ADMISSIBILITY_VERDICT not in combined
    assert not re.search(
        r"(?i)(?:summary.*(?:printed|shown|displayed|rendered|produced)|"
        r"(?:printed|shown|displayed|rendered|produced).*summary)",
        combined,
    )
    assert _tree_digests(target) == before


def test_remote_direct_skill_dry_run_prints_upgrade_consent_summary(
    tmp_path, tmp_path_factory, monkeypatch, capsys
):
    storage = tmp_path_factory.mktemp("direct-upgrade-dry-run-consent")
    acquisition = GitHttpsAcquisitionFake(monkeypatch, storage)
    source_tree = tmp_path / "source"
    skill = _write_direct_skill(source_tree)
    source = "git+https://github.com/example/skills@release"
    acquisition.publish("example/skills", "release", source_tree, revision="1" * 40)
    target = tmp_path / "target"
    assert _install_direct(source, target) == 0
    capsys.readouterr()
    (skill / "SKILL.md").write_text(
        "---\nname: example\n---\n# second\n", encoding="utf-8"
    )
    acquisition.publish("example/skills", "release", source_tree, revision="2" * 40)
    acquisition.calls.clear()
    before = _tree_digests(target)

    assert _upgrade_direct(target, "--dry-run") == 0
    summary = capsys.readouterr()
    assert acquisition.calls == [source]
    body = _publisher_block_body(summary.err)
    for label in (
        "selection",
        "source",
        "revision",
        "digest",
        "stored revision",
        "re-resolved revision",
        "stored digest",
        "re-resolved digest",
        "scope",
        "adapter",
        "destination",
    ):
        assert re.search(rf"(?m)^\s*{re.escape(label)}:\s+\S", body)
    assert _tree_digests(target) == before


def test_direct_skill_declined_confirmation_preserves_state_and_projection(
    tmp_path, monkeypatch, capsys
):
    source = tmp_path / "source"
    target = tmp_path / "target"
    skill = _write_direct_skill(source)
    payloads = {
        "scripts/run.py": b"print('first')\n",
        "references/guide.md": b"first reference\n",
        "assets/data.txt": b"first asset\n",
        "evals/case.txt": b"first evaluation\n",
    }
    for relpath, content in payloads.items():
        path = skill / relpath
        path.parent.mkdir(exist_ok=True)
        path.write_bytes(content)
    assert _install_direct(source, target) == 0
    capsys.readouterr()
    state_path = target / ".agentbundle-state.toml"
    projection = target / ".claude/skills/example"
    state_before = state_path.read_bytes()
    projection_before = _tree_digests(projection)
    assert set(projection_before) == {"SKILL.md", *payloads}
    (skill / "SKILL.md").write_text(
        "---\nname: example\n---\n# second\n", encoding="utf-8"
    )
    (skill / "scripts/run.py").write_text("print('second')\n", encoding="utf-8")
    (skill / "references/guide.md").unlink()
    (skill / "assets/new.txt").write_text("new asset\n", encoding="utf-8")
    (skill / "evals/case.txt").write_text("second evaluation\n", encoding="utf-8")
    prompts: list[str] = []
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)

    def _decline(prompt: str = "") -> str:
        prompts.append(prompt)
        return "n"

    monkeypatch.setattr("builtins.input", _decline)

    assert _upgrade_direct(target) == 1
    capsys.readouterr()
    assert prompts == ["\nUpgrade these skills? [y/N] "]
    assert state_path.read_bytes() == state_before
    assert _tree_digests(projection) == projection_before


def test_direct_skill_upgrade_consent_names_stored_and_resolved_identity(
    tmp_path, tmp_path_factory, monkeypatch, capsys
):
    from agentbundle.config import load_state

    storage = tmp_path_factory.mktemp("direct-upgrade-identity-consent")
    acquisition = GitHttpsAcquisitionFake(monkeypatch, storage)
    source_tree = tmp_path / "source"
    skill = _write_direct_skill(source_tree)
    source = "git+https://github.com/example/skills@release"
    stored_revision = "1" * 40
    resolved_revision = "2" * 40
    acquisition.publish(
        "example/skills", "release", source_tree, revision=stored_revision
    )
    target = tmp_path / "target"
    assert _install_direct(source, target) == 0
    capsys.readouterr()
    state_path = target / ".agentbundle-state.toml"
    stored = load_state(state_path).row("example", "claude-code")
    assert stored is not None
    assert stored.source_digest is not None
    (skill / "SKILL.md").write_text(
        "---\nname: example\n---\n# second\n", encoding="utf-8"
    )
    resolved_digest = _source_tree_digest(source_tree)
    acquisition.publish(
        "example/skills", "release", source_tree, revision=resolved_revision
    )

    assert _upgrade_direct(target, "--yes") == 0
    consent = _publisher_block_body(capsys.readouterr().err)
    assert stored.source_revision == stored_revision
    assert stored.source_revision != resolved_revision
    assert stored.source_digest != resolved_digest
    expected = {
        "source": source,
        "selection": "example",
        "stored revision": stored_revision,
        "re-resolved revision": resolved_revision,
        "stored digest": stored.source_digest,
        "re-resolved digest": resolved_digest,
        "scope": "repo",
        "adapter": "claude-code",
        "destination": str(target / ".claude/skills/example"),
    }
    for label, value in expected.items():
        assert re.search(
            rf"(?m)^\s*{re.escape(label)}:\s+{re.escape(value)}$", consent
        )


def test_local_direct_skill_requires_yes_before_replacement(tmp_path, capsys):
    source = tmp_path / "source"
    target = tmp_path / "target"
    skill = _write_direct_skill(source)
    assert _install_direct(source, target) == 0
    capsys.readouterr()
    (skill / "SKILL.md").write_text("---\nname: example\n---\n# second\n")
    before = _tree_digests(target)

    assert _upgrade_direct(target) == 1
    refusal = capsys.readouterr()
    assert "CAT-D008" in refusal.err
    assert "refusing to upgrade a standalone skill without confirmation" in refusal.err
    assert "install: refusing to install" not in refusal.err
    assert _tree_digests(target) == before


@pytest.mark.parametrize("flags", [(), ("--dry-run",)])
def test_direct_skill_no_update_reports_stdout(tmp_path, capsys, flags):
    source = tmp_path / "source"
    target = tmp_path / "target"
    _write_direct_skill(source)
    assert _install_direct(source, target) == 0
    capsys.readouterr()
    before = _tree_digests(target)

    assert _upgrade_direct(target, *flags) == 0
    captured = capsys.readouterr()
    assert "No update available for example." in captured.out
    assert "upgrade plan" not in captured.out
    assert _tree_digests(target) == before


def test_direct_skill_no_update_still_refuses_adopter_edit(tmp_path, capsys):
    source = tmp_path / "source"
    target = tmp_path / "target"
    _write_direct_skill(source)
    assert _install_direct(source, target) == 0
    capsys.readouterr()
    projection = target / ".claude/skills/example/SKILL.md"
    projection.write_text("# adopter edit\n")
    before = _tree_digests(target)

    assert _upgrade_direct(target, "--yes") == 1
    refusal = capsys.readouterr()
    assert "CAT-D027" in refusal.err
    assert "No update available" not in refusal.out
    assert _tree_digests(target) == before


def test_direct_skill_upgrade_replaces_only_invalidated_row_fields_once(
    tmp_path, monkeypatch, capsys
):
    from dataclasses import asdict

    from agentbundle import statelock
    from agentbundle.config import load_state

    source = tmp_path / "source"
    target = tmp_path / "target"
    skill = _write_direct_skill(source)
    assert _install_direct(source, target) == 0
    capsys.readouterr()
    state_path = target / ".agentbundle-state.toml"
    before_row = load_state(state_path).row("example", "claude-code")
    assert before_row is not None
    before = asdict(before_row)
    (skill / "SKILL.md").write_text("---\nname: example\n---\n# second\n")

    calls = 0
    persist = statelock.persist_state_locked

    def _counting_persist(*args, **kwargs):
        nonlocal calls
        calls += 1
        return persist(*args, **kwargs)

    with monkeypatch.context() as patcher:
        patcher.setattr(statelock, "persist_state_locked", _counting_persist)
        assert _upgrade_direct(target, "--yes") == 0
    assert calls == 1
    capsys.readouterr()

    after_row = load_state(state_path).row("example", "claude-code")
    assert after_row is not None
    after = asdict(after_row)
    fresh_target = tmp_path / "fresh-target"
    assert _install_direct(source, fresh_target) == 0
    fresh_row = load_state(fresh_target / ".agentbundle-state.toml").row(
        "example", "claude-code"
    )
    assert fresh_row is not None
    fresh = asdict(fresh_row)
    rewritten = {"source", "source_revision", "source_digest", "files"}
    for field in before.keys() - rewritten:
        assert after[field] == before[field] == fresh[field]
    assert after["source"] == before["source"] == fresh["source"]
    assert after["source_revision"] == fresh["source_revision"]
    assert after["source_digest"] == fresh["source_digest"]
    assert after["files"] == fresh["files"]
    assert after["source_digest"] != before["source_digest"]

    capsys.readouterr()
    assert _upgrade_direct(target, "--yes") == 0
    assert "No update available for example." in capsys.readouterr().out


def test_uncomparable_digest_refusal_preserves_bytes_and_executes_recovery(
    tmp_path, monkeypatch, capsys
):
    from agentbundle.config import load_state

    source = tmp_path / "source"
    target = tmp_path / "target"
    _write_direct_skill(source)
    assert _install_direct(source, target) == 0
    capsys.readouterr()
    stored = "sha512-1:" + "a" * 128
    _set_direct_source_digest(target, stored)
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)

    assert _upgrade_direct(target, "--yes") == 1
    refusal = capsys.readouterr()
    assert "CAT-D032" in refusal.err
    row = load_state(target / ".agentbundle-state.toml").row(
        "example", "claude-code"
    )
    assert row is not None
    assert row.source_digest == stored
    command_line = next(
        line.split("Then run: ", 1)[1]
        for line in refusal.err.splitlines()
        if "Then run: " in line
    )
    remove_command, install_command = command_line.split(" then ", 1)
    assert _run_printed_command(remove_command) == 0
    assert _run_printed_command(install_command) == 0
    repaired = load_state(target / ".agentbundle-state.toml").row(
        "example", "claude-code"
    )
    assert repaired is not None
    assert repaired.source_digest is not None
    assert repaired.source_digest.startswith("sha256-1:")
    assert repaired.source_digest != stored


def test_remote_consent_refusal_precedes_uncomparable_digest(
    tmp_path, tmp_path_factory, monkeypatch, capsys
):
    storage = tmp_path_factory.mktemp("direct-upgrade-consent-before-digest")
    acquisition = GitHttpsAcquisitionFake(monkeypatch, storage)
    source_tree = tmp_path / "source"
    _write_direct_skill(source_tree)
    source = "git+https://github.com/example/skills@release"
    acquisition.publish("example/skills", "release", source_tree)
    target = tmp_path / "target"
    assert _install_direct(source, target) == 0
    capsys.readouterr()
    _set_direct_source_digest(target, "sha512-1:" + "a" * 128)

    assert _upgrade_direct(target) == 1
    refusal = capsys.readouterr()
    assert "CAT-D008" in refusal.err
    assert "CAT-D032" not in refusal.err


@pytest.mark.parametrize(
    ("moved_field", "moved_value"),
    [
        ("source_path", "skills/concurrent"),
        ("source_digest", "sha256-1:" + "f" * 64),
    ],
)
def test_direct_skill_upgrade_refuses_when_locked_row_moved(
    tmp_path, monkeypatch, capsys, moved_field, moved_value
):
    from agentbundle import statelock
    from agentbundle.config import dump_state, load_state

    source = tmp_path / "source"
    target = tmp_path / "target"
    skill = _write_direct_skill(source)
    assert _install_direct(source, target) == 0
    capsys.readouterr()
    (skill / "SKILL.md").write_text("---\nname: example\n---\n# second\n")
    state_path = target / ".agentbundle-state.toml"
    persist = statelock.persist_state_locked

    def _move_then_persist(path, mutate, **kwargs):
        state = load_state(path)
        row = state.row("example", "claude-code")
        assert row is not None
        setattr(row, moved_field, moved_value)
        path.write_text(dump_state(state), encoding="utf-8", newline="\n")
        return persist(path, mutate, **kwargs)

    monkeypatch.setattr(statelock, "persist_state_locked", _move_then_persist)
    assert _upgrade_direct(target, "--yes") == 1
    refusal = capsys.readouterr()
    assert "state write failed" in refusal.err
    moved = load_state(state_path).row("example", "claude-code")
    assert moved is not None
    assert getattr(moved, moved_field) == moved_value


def test_direct_skill_dry_run_prints_plan_without_mutation(tmp_path, capsys):
    source = tmp_path / "source"
    target = tmp_path / "target"
    skill = _write_direct_skill(source)
    assert _install_direct(source, target) == 0
    capsys.readouterr()

    state_path = target / ".agentbundle-state.toml"
    projection = target / ".claude/skills/example/SKILL.md"
    state_before = hashlib.sha256(state_path.read_bytes()).digest()
    projection_before = hashlib.sha256(projection.read_bytes()).digest()
    (skill / "SKILL.md").write_text("---\nname: example\n---\n# second\n")

    assert _upgrade_direct(target, "--dry-run") == 0
    captured = capsys.readouterr()
    assert "upgrade plan" in captured.out
    assert hashlib.sha256(state_path.read_bytes()).digest() == state_before
    assert hashlib.sha256(projection.read_bytes()).digest() == projection_before


@pytest.mark.parametrize(
    ("before", "after"),
    [
        ("allowed-tools: Read", "allowed-tools: Read, Bash"),
        ("allowed-tools: Read", ""),
        ("allowed-tools: Read", "allowed-tools: []"),
        ("allowed-tools: Read", 'allowed-tools: ""'),
        ("", "metadata:\n  boundaries:\n    - network"),
        ("", "metadata:\n  credentialed: true"),
        ("metadata:\n  credentialed: false", 'metadata:\n  credentialed: "yes"'),
    ],
    ids=(
        "allowed-tool-added",
        "allowed-tools-absent",
        "allowed-tools-empty-list",
        "allowed-tools-empty-string",
        "boundary-added",
        "credentialed-undeclared-to-true",
        "credentialed-open-value",
    ),
)
def test_direct_skill_capability_widening_refuses_without_writing(
    tmp_path, capsys, before, after
):
    source = tmp_path / "source"
    target = tmp_path / "target"
    skill = _write_capability_skill(source, before, "# first\n")
    assert _install_direct(source, target) == 0
    capsys.readouterr()
    state_path = target / ".agentbundle-state.toml"
    projection = target / ".claude/skills/example/SKILL.md"
    state_before = hashlib.sha256(state_path.read_bytes()).digest()
    projection_before = hashlib.sha256(projection.read_bytes()).digest()

    _write_capability_skill(source, after, "# second\n")
    assert skill.exists()
    assert _upgrade_direct(target, "--yes") == 1

    refusal = capsys.readouterr()
    assert "CAT-D031" in refusal.err
    assert "capability" in refusal.err
    assert hashlib.sha256(state_path.read_bytes()).digest() == state_before
    assert hashlib.sha256(projection.read_bytes()).digest() == projection_before


@pytest.mark.parametrize(
    ("before", "after"),
    [
        ("", "allowed-tools: Read"),
        ("metadata:\n  boundaries:\n    - network", ""),
        ("metadata:\n  credentialed: true", "metadata:\n  credentialed: false"),
    ],
    ids=("allowed-tools", "boundaries", "credentialed"),
)
def test_direct_skill_capability_narrowing_proceeds(tmp_path, capsys, before, after):
    source = tmp_path / "source"
    target = tmp_path / "target"
    _write_capability_skill(source, before, "# first\n")
    assert _install_direct(source, target) == 0
    capsys.readouterr()

    skill = _write_capability_skill(source, after, "# second\n")
    assert _upgrade_direct(target, "--yes") == 0
    assert (target / ".claude/skills/example/SKILL.md").read_bytes() == (
        skill / "SKILL.md"
    ).read_bytes()


def test_direct_skill_reports_every_capability_widening_before_confirmation(
    tmp_path, capsys
):
    source = tmp_path / "source"
    target = tmp_path / "target"
    _write_capability_skill(
        source,
        "allowed-tools: Read\nmetadata:\n  credentialed: false",
        "# first\n",
    )
    assert _install_direct(source, target) == 0
    capsys.readouterr()
    _write_capability_skill(
        source,
        "allowed-tools: Read, Bash\n"
        "metadata:\n"
        "  boundaries:\n"
        "    - network\n"
        '  credentialed: "yes"',
        "# second\n",
    )

    assert _upgrade_direct(target) == 1
    refusal = capsys.readouterr()
    assert "CAT-D031" in refusal.err
    assert "allowed-tools adds Bash" in refusal.err
    assert "boundaries adds network" in refusal.err
    assert "credentialed moves from false to yes" in refusal.err
    assert "CAT-D008" not in refusal.err


def test_adopter_edit_and_capability_refusals_are_both_reported_in_order(
    tmp_path, capsys
):
    source = tmp_path / "source"
    target = tmp_path / "target"
    _write_capability_skill(source, "allowed-tools: Read", "# first\n")
    assert _install_direct(source, target) == 0
    capsys.readouterr()
    projection = target / ".claude/skills/example/SKILL.md"
    projection.write_text("# adopter edit\n", encoding="utf-8")
    before = _tree_digests(target)
    _write_capability_skill(source, "allowed-tools: Read, Bash", "# second\n")

    assert _upgrade_direct(target, "--yes") == 1
    refusal = capsys.readouterr()
    assert refusal.err.index("CAT-D027") < refusal.err.index("CAT-D031")
    assert refusal.err.count("Move the adopter-edited file aside") == 1
    assert _tree_digests(target) == before


def test_direct_skill_payload_only_change_with_unsafe_capability_proceeds(
    tmp_path, capsys
):
    source = tmp_path / "source"
    target = tmp_path / "target"
    skill = _write_capability_skill(
        source, "metadata:\n  credentialed: true", "# unchanged\n"
    )
    payload = skill / "references" / "guide.md"
    payload.parent.mkdir()
    payload.write_text("first\n", encoding="utf-8")
    assert _install_direct(source, target) == 0
    capsys.readouterr()

    payload.write_text("second\n", encoding="utf-8")
    assert _upgrade_direct(target, "--yes") == 0
    assert (
        target / ".claude/skills/example/references/guide.md"
    ).read_text(encoding="utf-8") == "second\n"


def test_projected_capability_axes_round_trip_all_three_axes(tmp_path, capsys):
    from agentbundle.config import load_state
    from agentbundle.direct_install import _read_projected_capability_axes

    source = tmp_path / "source"
    target = tmp_path / "target"
    _write_capability_skill(
        source,
        'allowed-tools: "Read, Bash"\n'
        "metadata:\n"
        "  boundaries:\n"
        "    - filesystem_read\n"
        '  credentialed: "yes"',
    )
    assert _install_direct(source, target) == 0
    capsys.readouterr()
    row = load_state(target / ".agentbundle-state.toml").row(
        "example", "claude-code"
    )
    assert row is not None
    relpath = ".claude/skills/example/SKILL.md"

    axes = _read_projected_capability_axes(target, relpath, row)

    assert axes is not None
    assert axes.allowed_tools == frozenset({"Bash", "Read"})
    assert axes.boundaries == frozenset({"filesystem_read"})
    assert axes.credentialed == "yes"


def test_projected_capability_axes_hashes_the_single_read_before_parsing(
    tmp_path, monkeypatch, capsys
):
    import agentbundle.bounded_metadata as bounded_metadata
    import agentbundle.direct_install as direct_install
    from agentbundle.catalogue_tooling import file_safety
    from agentbundle.config import load_state

    source = tmp_path / "source"
    target = tmp_path / "target"
    _write_capability_skill(source, "allowed-tools: Read", "# first\n")
    assert _install_direct(source, target) == 0
    capsys.readouterr()
    row = load_state(target / ".agentbundle-state.toml").row(
        "example", "claude-code"
    )
    assert row is not None
    relpath = ".claude/skills/example/SKILL.md"
    real_read = file_safety.read_confined_regular_file
    real_sha256 = direct_install.hashlib.sha256
    real_parse = bounded_metadata.parse_bounded_metadata
    events: list[str] = []
    read_objects: list[bytes] = []
    hashed_objects: list[bytes] = []
    parsed_objects: list[bytes] = []

    def observed_read(*args, **kwargs):
        data = real_read(*args, **kwargs)
        events.append("read")
        read_objects.append(data)
        return data

    def observed_sha256(data=b"", **kwargs):
        events.append("hash")
        hashed_objects.append(data)
        return real_sha256(data, **kwargs)

    def observed_parse(data, *args, **kwargs):
        events.append("parse")
        parsed_objects.append(data)
        return real_parse(data, *args, **kwargs)

    monkeypatch.setattr(file_safety, "read_confined_regular_file", observed_read)
    monkeypatch.setattr(direct_install.hashlib, "sha256", observed_sha256)
    monkeypatch.setattr(bounded_metadata, "parse_bounded_metadata", observed_parse)

    axes = direct_install._read_projected_capability_axes(target, relpath, row)

    assert axes is not None
    assert events == ["read", "hash", "parse"]
    assert len(read_objects) == 1
    assert hashed_objects[0] is read_objects[0]
    assert parsed_objects[0] is hashed_objects[0]


def test_projected_capability_axes_does_not_parse_a_digest_mismatch(
    tmp_path, monkeypatch, capsys
):
    import agentbundle.bounded_metadata as bounded_metadata
    import agentbundle.direct_install as direct_install
    from agentbundle.config import load_state

    source = tmp_path / "source"
    target = tmp_path / "target"
    _write_capability_skill(source, "allowed-tools: Read", "# first\n")
    assert _install_direct(source, target) == 0
    capsys.readouterr()
    row = load_state(target / ".agentbundle-state.toml").row(
        "example", "claude-code"
    )
    assert row is not None
    relpath = ".claude/skills/example/SKILL.md"
    (target / relpath).write_bytes(
        b"---\nname: example\nallowed-tools: Read, Bash\n---\n# second\n"
    )
    parse_calls: list[bytes] = []
    real_parse = bounded_metadata.parse_bounded_metadata

    def observed_parse(data, *args, **kwargs):
        parse_calls.append(data)
        return real_parse(data, *args, **kwargs)

    monkeypatch.setattr(bounded_metadata, "parse_bounded_metadata", observed_parse)

    axes = direct_install._read_projected_capability_axes(target, relpath, row)

    assert axes is None
    assert parse_calls == []


def test_malformed_integrity_bound_projection_is_unknown_and_refuses(tmp_path, capsys):
    source = tmp_path / "source"
    target = tmp_path / "target"
    skill = _write_capability_skill(source, "allowed-tools: Read", "# first\n")
    assert _install_direct(source, target) == 0
    capsys.readouterr()
    state_path = target / ".agentbundle-state.toml"
    relpath = ".claude/skills/example/SKILL.md"
    projection = target / relpath
    projection.write_bytes(b"not frontmatter\n")
    _set_recorded_file_sha(
        target, relpath, hashlib.sha256(projection.read_bytes()).hexdigest()
    )
    state_before = hashlib.sha256(state_path.read_bytes()).digest()
    projection_before = hashlib.sha256(projection.read_bytes()).digest()
    _write_capability_skill(source, "allowed-tools: Read", "# second\n")
    assert skill.exists()

    assert _upgrade_direct(target, "--yes") == 1
    refusal = capsys.readouterr()
    assert "CAT-D031" in refusal.err
    assert "unknown" in refusal.err
    assert hashlib.sha256(state_path.read_bytes()).digest() == state_before
    assert hashlib.sha256(projection.read_bytes()).digest() == projection_before


def test_missing_projected_capability_surface_is_unknown_and_refuses(tmp_path, capsys):
    source = tmp_path / "source"
    target = tmp_path / "target"
    _write_capability_skill(source, "allowed-tools: Read", "# first\n")
    assert _install_direct(source, target) == 0
    capsys.readouterr()
    state_path = target / ".agentbundle-state.toml"
    projection = target / ".claude/skills/example/SKILL.md"
    projection.unlink()
    state_before = hashlib.sha256(state_path.read_bytes()).digest()
    _write_capability_skill(source, "allowed-tools: Read", "# second\n")

    assert _upgrade_direct(target, "--yes") == 1
    refusal = capsys.readouterr()
    assert "CAT-D031" in refusal.err
    assert "unknown" in refusal.err
    assert hashlib.sha256(state_path.read_bytes()).digest() == state_before
    assert not projection.exists()


def test_capability_refusal_integrity_binding_and_remediation_pins_wanted_revision(
    tmp_path, tmp_path_factory, monkeypatch, capsys
):
    from agentbundle.config import load_state

    storage = tmp_path_factory.mktemp("direct-capability-remediation")
    acquisition = GitHttpsAcquisitionFake(monkeypatch, storage)
    user_root = tmp_path / "user root"
    monkeypatch.setenv("HOME", str(user_root))
    monkeypatch.setenv("AGENTBUNDLE_USER_ROOT", str(user_root))
    source_tree = tmp_path / "source"
    skill = _write_capability_skill(source_tree, "allowed-tools: Read", "# first\n")
    obsolete = skill / "references" / "obsolete.md"
    obsolete.parent.mkdir()
    obsolete.write_text("old\n", encoding="utf-8")
    source = "git+https://github.com/example/skills@release"
    first_revision = acquisition.publish("example/skills", "release", source_tree)
    target = tmp_path / "command root"
    assert _install_direct(source, target, scope="user", adapter="codex") == 0
    capsys.readouterr()

    wanted_skill = _write_capability_skill(
        source_tree, "allowed-tools: Read, Bash", "# wanted\n"
    )
    obsolete.unlink()
    wanted_revision = acquisition.publish("example/skills", "release", source_tree)
    acquisition.publish(
        "example/skills",
        wanted_revision,
        source_tree,
        revision=wanted_revision,
    )
    assert wanted_revision != first_revision
    projection = user_root / ".agents/skills/example/SKILL.md"
    incoming = (wanted_skill / "SKILL.md").read_bytes()
    projection.write_bytes(incoming)
    state_path = user_root / ".agentbundle/state.toml"
    state_before = hashlib.sha256(state_path.read_bytes()).digest()
    projection_before = hashlib.sha256(projection.read_bytes()).digest()

    assert _upgrade_direct(
        target, "--scope", "user", "--adapter", "codex", "--yes"
    ) == 1
    refusal = capsys.readouterr()
    assert "CAT-D031" in refusal.err
    assert "unknown" in refusal.err
    assert hashlib.sha256(state_path.read_bytes()).digest() == state_before
    assert hashlib.sha256(projection.read_bytes()).digest() == projection_before
    recovery = next(
        line.split("Then run: ", 1)[1]
        for line in refusal.err.splitlines()
        if "Then run: " in line
    )
    uninstall_command, install_command = recovery.split(" then ", 1)

    _write_capability_skill(source_tree, "allowed-tools: Read, Bash", "# moved\n")
    moved_revision = acquisition.publish("example/skills", "release", source_tree)
    assert moved_revision != wanted_revision

    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    kept_edit = tmp_path / "kept incoming projection.md"
    kept_edit.write_bytes(projection.read_bytes())
    projection.unlink()
    assert _run_printed_command(uninstall_command) == 0
    assert _run_printed_command(install_command) == 0

    state = load_state(state_path)
    row = state.row("example", "codex")
    assert row is not None
    assert row.source_revision == wanted_revision
    assert acquisition.calls[-1] == (
        f"git+https://github.com/example/skills@{wanted_revision}"
    )
    assert projection.read_bytes() == incoming
    assert kept_edit.read_bytes() == incoming
    assert not (user_root / ".agents/skills/example/references/obsolete.md").exists()
    projected_files = {
        path.relative_to(user_root).as_posix()
        for path in user_root.rglob("*")
        if path.is_file() and path != state_path
    }
    assert projected_files
    assert all(state.owners_of(relpath) for relpath in projected_files)


# ---------------------------------------------------------------------------
# 1. Whole-pack upgrade: installed-version updated; files are 0.2.0 content
# ---------------------------------------------------------------------------


def test_whole_pack_upgrade_updates_version_and_content(tmp_path):
    """Whole-pack upgrade from 0.1.0 to 0.2.0 must update installed-version and
    rewrite every Tier-1 projected file to the 0.2.0 content."""
    from agentbundle.config import load_state
    from agentbundle.render import render_pack

    rc = _install_v1(tmp_path)
    assert rc == 0, "install of 0.1.0 must succeed"

    rc = _run_upgrade(
        pack="core",
        catalogue=str(CAT_V2),
        root=str(tmp_path),
    )
    assert rc == 0, "whole-pack upgrade must succeed"

    # installed-version must be updated.
    state = load_state(tmp_path / ".agentbundle-state.toml")
    assert state.row("core", "claude-code").installed_version == "0.2.0"

    # All projected files must now have 0.2.0 content.
    v2_projection = render_pack(PACK_V2)
    for relpath, expected_bytes in v2_projection.items():
        on_disk = tmp_path / relpath
        assert on_disk.exists(), f"expected {relpath!r} to exist after upgrade"
        assert on_disk.read_bytes() == expected_bytes, (
            f"file {relpath!r} must contain 0.2.0 content"
        )


# ---------------------------------------------------------------------------
# 2. Per-primitive upgrade — parametrised over the five flag types
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "flag_attr, prim_name, prim_type, src_dir",
    [
        ("skill", "work-loop", "skill", "skills"),
        ("agent", "reviewer", "agent", "agents"),
        ("hook", "pre-commit", "hook-body", "hooks"),
        ("seed", None, "seed", "seeds"),  # skip; no seeds in fixture
        ("command", "deploy", "command", "commands"),
    ],
)
def test_per_primitive_upgrade_moves_only_matching_files(
    tmp_path, flag_attr, prim_name, prim_type, src_dir
):
    """A per-primitive upgrade must update only files matching the primitive
    and record the override in state under [pack.core.<ptype>.<pname>]."""
    if prim_name is None:
        pytest.skip("no seed primitives in core fixture; skip")

    from agentbundle.commands.upgrade import _filter_for_primitive
    from agentbundle.config import load_state
    from agentbundle.render import render_pack

    rc = _install_v1(tmp_path)
    assert rc == 0

    v1_projection = render_pack(PACK_V1)
    v2_projection = render_pack(PACK_V2)
    prim_paths = set(_filter_for_primitive(v2_projection, prim_name, src_dir).keys())
    # --hook co-moves the matching hook-wiring of the same name.
    if flag_attr == "hook":
        prim_paths |= set(_filter_for_primitive(v2_projection, prim_name, "hook-wiring").keys())
    non_prim_paths = set(v1_projection.keys()) - prim_paths

    # Capture v1 content for non-matching paths before upgrade.
    non_prim_before = {
        rp: (tmp_path / rp).read_bytes() for rp in non_prim_paths if (tmp_path / rp).exists()
    }

    kwargs: dict = {"pack": "core", "catalogue": str(CAT_V2), "root": str(tmp_path)}
    kwargs[flag_attr] = prim_name
    rc = _run_upgrade(**kwargs)
    assert rc == 0, f"per-primitive upgrade --{flag_attr} {prim_name} must succeed"

    # Matching files must be 0.2.0 content.
    for relpath in sorted(prim_paths):
        on_disk = tmp_path / relpath
        assert on_disk.exists(), f"expected {relpath!r} after upgrade"
        assert on_disk.read_bytes() == v2_projection[relpath], (
            f"{relpath!r} must contain 0.2.0 content"
        )

    # Non-matching files must be 0.1.0 content (unchanged).
    for rp, before_bytes in non_prim_before.items():
        assert (tmp_path / rp).read_bytes() == before_bytes, (
            f"non-primitive file {rp!r} must not change"
        )

    # State must have primitive_versions entry.
    state = load_state(tmp_path / ".agentbundle-state.toml")
    pv = state.row("core", "claude-code").primitive_versions
    assert prim_type in pv, f"primitive_versions must contain {prim_type!r}"
    assert pv[prim_type].get(prim_name) == "0.2.0", (
        f"primitive_versions[{prim_type!r}][{prim_name!r}] must be '0.2.0'"
    )

    # Pack-level installed-version must NOT be updated on per-primitive upgrade.
    assert state.row("core", "claude-code").installed_version == "0.1.0", (
        "installed-version must stay at 0.1.0 for a per-primitive upgrade"
    )


# ---------------------------------------------------------------------------
# 3. Mixed-version warning: per-primitive upgrade then whole-pack → warning
# ---------------------------------------------------------------------------


def test_mixed_version_warning_on_whole_pack_after_per_primitive(tmp_path, capsys):
    """After upgrading --skill to 0.2.0, a whole-pack upgrade to 0.3.0 must
    print a warning to stderr about mixed-version primitives before proceeding."""
    rc = _install_v1(tmp_path)
    assert rc == 0

    # Per-primitive upgrade of skill to 0.2.0.
    rc = _run_upgrade(
        pack="core",
        catalogue=str(CAT_V2),
        root=str(tmp_path),
        skill="work-loop",
    )
    assert rc == 0

    # Clear captured output before the whole-pack upgrade.
    capsys.readouterr()

    # Whole-pack upgrade to 0.3.0 — must warn.
    rc = _run_upgrade(
        pack="core",
        catalogue=str(CAT_V3),
        root=str(tmp_path),
    )
    assert rc == 0

    captured = capsys.readouterr()
    assert "mixed-version" in captured.err, (
        "stderr must contain 'mixed-version' when pack has per-primitive overrides"
    )
    assert "work-loop" in captured.err, "stderr must name the mixed-version primitive"


# ---------------------------------------------------------------------------
# 4. Primitive-not-found: exit non-zero with expected message
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "flag_attr",
    ["skill", "agent", "hook", "seed", "command"],
)
def test_primitive_not_found_exits_nonzero(tmp_path, capsys, flag_attr):
    """``--<flag> foo`` where foo is not in the pack must exit non-zero with
    a one-line stderr ``primitive 'foo' not in pack core``."""
    rc = _install_v1(tmp_path)
    assert rc == 0

    kwargs = {
        "pack": "core",
        "catalogue": str(CAT_V2),
        "root": str(tmp_path),
    }
    kwargs[flag_attr] = "foo"
    rc = _run_upgrade(**kwargs)
    assert rc != 0, f"--{flag_attr} foo must exit non-zero"
    captured = capsys.readouterr()
    assert "primitive 'foo' not in pack core" in captured.err, (
        f"stderr must say \"primitive 'foo' not in pack core\"; got: {captured.err!r}"
    )


# ---------------------------------------------------------------------------
# 5. Hook-extension preservation: .sh stays .sh; .py stays .py
# ---------------------------------------------------------------------------


def test_hook_extension_preservation_sh(tmp_path):
    """Upgrading a .sh hook retains the .sh extension."""
    rc = _install_v1(tmp_path)
    assert rc == 0

    rc = _run_upgrade(
        pack="core",
        catalogue=str(CAT_V2),
        root=str(tmp_path),
        hook="pre-commit",
    )
    assert rc == 0

    # pre-commit.sh must exist on disk (not .sh.py or any other extension).
    sh_files = list(tmp_path.rglob("pre-commit.sh"))
    assert sh_files, "pre-commit.sh must still exist after --hook upgrade"

    # Must not have mutated extension.
    for f in sh_files:
        assert f.suffix == ".sh", f"expected .sh extension, got {f.suffix}"


def test_hook_upgrade_co_moves_wiring(tmp_path):
    """`--hook <name>` is atomic over hook-body AND matching hook-wiring.

    The wiring co-moves with its body so a per-hook
    upgrade can never land a torn pair (a new hook script paired with
    the previous matcher/event wiring). The v1→v2 fixture diff includes
    a wiring change (`matcher = "Bash"` → `matcher = "Bash|Edit"`); a
    successful `--hook pre-commit --to 0.2.0` must produce the v2
    wiring content on disk.
    """
    rc = _install_v1(tmp_path)
    assert rc == 0

    rc = _run_upgrade(
        pack="core",
        catalogue=str(CAT_V2),
        root=str(tmp_path),
        hook="pre-commit",
    )
    assert rc == 0

    # The hook-wiring file is projected under `apm/core/.apm/hook-wiring/`.
    wiring_files = list(tmp_path.rglob("hook-wiring/pre-commit.toml"))
    assert wiring_files, "hook-wiring/pre-commit.toml must be co-moved"
    contents = wiring_files[0].read_text(encoding="utf-8")
    assert 'matcher = "Bash|Edit"' in contents, (
        f"--hook pre-commit must co-move wiring; got:\n{contents}"
    )


def test_hook_extension_preservation_py(tmp_path):
    """Upgrading a .py hook retains the .py extension."""
    rc = _install_v1(tmp_path)
    assert rc == 0

    rc = _run_upgrade(
        pack="core",
        catalogue=str(CAT_V2),
        root=str(tmp_path),
        hook="lint",
    )
    assert rc == 0

    py_files = list(tmp_path.rglob("lint.py"))
    assert py_files, "lint.py must still exist after --hook lint upgrade"
    for f in py_files:
        assert f.suffix == ".py", f"expected .py extension, got {f.suffix}"


# ---------------------------------------------------------------------------
# 6. Pack-not-installed: exit non-zero with message
# ---------------------------------------------------------------------------


def test_pack_not_installed_exits_nonzero(tmp_path, capsys):
    """Upgrading a pack that was never installed must exit non-zero."""
    # No install — empty state.
    rc = _run_upgrade(
        pack="core",
        catalogue=str(CAT_V2),
        root=str(tmp_path),
    )
    assert rc != 0
    captured = capsys.readouterr()
    assert "not installed" in captured.err


# ---------------------------------------------------------------------------
# 7. Success recap — upgrade must print a one-line recap to stdout on
#    success, mirroring install/uninstall. Regression: shipped silent in
#    cd4f3e58; users couldn't tell whether an upgrade had taken effect.
# ---------------------------------------------------------------------------


def test_whole_pack_upgrade_prints_success_recap(tmp_path, capsys):
    """A successful whole-pack upgrade must emit a one-line recap on stdout
    naming the pack and the target version. Regression test for the
    silent-success bug — stdout must not be empty on the happy path."""
    rc = _install_v1(tmp_path)
    assert rc == 0
    capsys.readouterr()  # drop install output

    rc = _run_upgrade(
        pack="core",
        catalogue=str(CAT_V2),
        root=str(tmp_path),
    )
    assert rc == 0

    captured = capsys.readouterr()
    assert captured.out.strip(), "whole-pack upgrade must print a non-empty recap to stdout"
    last = captured.out.strip().splitlines()[-1]
    assert last.startswith("upgraded:"), f"recap must start with 'upgraded:'; got: {last!r}"
    assert "core" in last and "0.2.0" in last, (
        f"recap must name pack and target version; got: {last!r}"
    )


def test_per_primitive_upgrade_prints_success_recap(tmp_path, capsys):
    """A successful per-primitive upgrade must emit a one-line recap on stdout
    naming the pack, the primitive, and the target version."""
    rc = _install_v1(tmp_path)
    assert rc == 0
    capsys.readouterr()

    rc = _run_upgrade(
        pack="core",
        catalogue=str(CAT_V2),
        root=str(tmp_path),
        skill="work-loop",
    )
    assert rc == 0

    captured = capsys.readouterr()
    assert captured.out.strip(), "per-primitive upgrade must print a non-empty recap to stdout"
    last = captured.out.strip().splitlines()[-1]
    assert last.startswith("upgraded:"), f"recap must start with 'upgraded:'; got: {last!r}"
    assert "core" in last and "work-loop" in last and "0.2.0" in last, (
        f"recap must name pack, primitive, and target version; got: {last!r}"
    )


def test_filter_for_primitive_refuses_ambiguous_name():
    """If a pack would project both `<src_dir>/<name>/...` and
    `<src_dir>/<name>.<ext>` for the same primitive name, `_filter_for_primitive`
    refuses with ValueError — F-build's `validate_pack_uniqueness` already
    rejects this shape at build time, but the upgrade boundary checks again."""
    from agentbundle.commands.upgrade import _filter_for_primitive

    projection = {
        "apm/core/.apm/skills/foo/SKILL.md": b"dir form",
        "apm/core/.apm/skills/foo.md": b"file form",
    }
    import pytest

    with pytest.raises(ValueError, match="ambiguous"):
        _filter_for_primitive(projection, "foo", "skills")


# ---------------------------------------------------------------------------
# 8. Tier-2 companion-drop visibility (upgrade-companion-visibility spec)
#    A file edited since install is detected Tier-2 on upgrade: the adopter's
#    edit is preserved, the upstream goes to a `.upstream.<ext>` companion, and
#    the operator is TOLD (count + companion path) on stderr — closing the
#    silent-companion diagnosability gap. Regression-paired with the
#    test_tier_invariants.py harness (never-clobber + companion-exists).
# ---------------------------------------------------------------------------

# Anchor on the production-unique header phrase so the positive and negative
# tests bind to the same load-bearing string (they drift together if reworded).
_COMPANION_NOTICE = "were modified since install and kept as *.upstream.<ext> companions"


def _first_projected_on_disk(root: Path, pack_dir: Path) -> str:
    """Pick a relpath the pack projects that exists on disk after install."""
    from agentbundle.render import render_pack

    for relpath in sorted(render_pack(pack_dir)):
        if (root / relpath).exists():
            return relpath
    raise AssertionError("no projected file found on disk after install")


def test_upgrade_tier2_collision_surfaces_companion_path(tmp_path, capsys):
    """A file edited since install must, on upgrade: stay byte-for-byte the
    adopter's (never clobbered), gain a `.upstream.<ext>` companion holding the
    upstream content, AND have its companion path named on stderr with the
    'kept as *.upstream.<ext> companions' notice."""
    from agentbundle import safety
    from agentbundle.render import render_pack

    rc = _install_v1(tmp_path)
    assert rc == 0
    capsys.readouterr()  # drop install output

    target_rel = _first_projected_on_disk(tmp_path, PACK_V2)
    adopter_bytes = b"# adopter edits -- do not clobber\n"
    (tmp_path / target_rel).write_bytes(adopter_bytes)  # forces Tier-2

    rc = _run_upgrade(pack="core", catalogue=str(CAT_V2), root=str(tmp_path))
    assert rc == 0, "upgrade over a Tier-2 collision must still succeed"

    # Never clobbered: the adopter's edit survives at the original path.
    assert (tmp_path / target_rel).read_bytes() == adopter_bytes, (
        "Tier-2 file must not be clobbered on upgrade"
    )

    # Upstream content went to the `.upstream.<ext>` companion.
    companion_rel = safety.companion_path(Path(target_rel))
    companion_on_disk = tmp_path / companion_rel
    assert companion_on_disk.exists(), f"expected companion {companion_rel}"
    assert companion_on_disk.read_bytes() == render_pack(PACK_V2)[target_rel], (
        "companion must hold the upstream (v2) content"
    )

    # The operator is TOLD: notice + count + the companion path on stderr.
    err = capsys.readouterr().err
    assert _COMPANION_NOTICE in err, (
        f"upgrade must announce the companion-drop on stderr; got: {err!r}"
    )
    assert "1 file(s)" in err, f"notice must name the count; got: {err!r}"
    assert companion_rel.as_posix() in err, (
        f"upgrade must name the companion path on stderr; got: {err!r}"
    )


def test_upgrade_without_collision_emits_no_companion_notice(tmp_path, capsys):
    """A clean install→upgrade (no adopter edits) is all Tier-1: no companion
    is dropped and no companion notice is printed."""
    rc = _install_v1(tmp_path)
    assert rc == 0
    capsys.readouterr()  # drop install output

    rc = _run_upgrade(pack="core", catalogue=str(CAT_V2), root=str(tmp_path))
    assert rc == 0

    err = capsys.readouterr().err
    assert _COMPANION_NOTICE not in err, (
        f"a collision-free upgrade must not print a companion notice; got: {err!r}"
    )


def test_upgrade_multiple_tier2_collisions_counts_and_lists_all(tmp_path, capsys):
    """Two files edited since install must both be preserved + companioned, and
    the notice must report the count (`2 file(s)`) and enumerate both companion
    paths — pins the count rendering and the plural-path branch."""
    from agentbundle import safety
    from agentbundle.render import render_pack

    rc = _install_v1(tmp_path)
    assert rc == 0
    capsys.readouterr()

    on_disk = [rp for rp in sorted(render_pack(PACK_V2)) if (tmp_path / rp).exists()]
    assert len(on_disk) >= 2, "fixture must project at least two files"
    targets = on_disk[:2]
    for rp in targets:
        (tmp_path / rp).write_bytes(f"# adopter edit of {rp}\n".encode())

    rc = _run_upgrade(pack="core", catalogue=str(CAT_V2), root=str(tmp_path))
    assert rc == 0

    err = capsys.readouterr().err
    assert "2 file(s)" in err, f"notice must report count 2; got: {err!r}"
    for rp in targets:
        companion_rel = safety.companion_path(Path(rp)).as_posix()
        assert companion_rel in err, (
            f"notice must list every companion path; missing {companion_rel}\n{err!r}"
        )
        # And every original is preserved (never clobbered).
        assert (tmp_path / rp).read_bytes() == f"# adopter edit of {rp}\n".encode()


def test_per_primitive_upgrade_surfaces_tier2_companion(tmp_path, capsys):
    """The companion notice also fires on a per-primitive (`--skill`) upgrade —
    the same shared walk handles both shapes. Edit a projected work-loop skill
    file, upgrade just that skill, and assert the companion + notice."""
    from agentbundle import safety
    from agentbundle.commands.upgrade import _filter_for_primitive
    from agentbundle.render import render_pack

    rc = _install_v1(tmp_path)
    assert rc == 0
    capsys.readouterr()

    skill_paths = [
        rp
        for rp in sorted(_filter_for_primitive(render_pack(PACK_V2), "work-loop", "skills"))
        if (tmp_path / rp).exists()
    ]
    assert skill_paths, "work-loop skill must project at least one file on disk"
    target_rel = skill_paths[0]
    (tmp_path / target_rel).write_bytes(b"# adopter-edited skill body\n")

    rc = _run_upgrade(
        pack="core",
        catalogue=str(CAT_V2),
        root=str(tmp_path),
        skill="work-loop",
    )
    assert rc == 0

    companion_rel = safety.companion_path(Path(target_rel))
    assert (tmp_path / companion_rel).exists(), "per-primitive upgrade must drop a companion"
    err = capsys.readouterr().err
    assert _COMPANION_NOTICE in err, f"per-primitive upgrade must announce it; got: {err!r}"
    assert companion_rel.as_posix() in err, f"must name the companion path; got: {err!r}"
    # Adopter edit preserved.
    assert (tmp_path / target_rel).read_bytes() == b"# adopter-edited skill body\n"


# ---------------------------------------------------------------------------
# Dry-run preview (projection-dry-run spec): read-only, writes nothing
# ---------------------------------------------------------------------------


def _snapshot_tree(root: Path) -> dict[str, bytes]:
    """Map every file under ``root`` to its bytes, for byte-identical asserts."""
    return {
        p.relative_to(root).as_posix(): p.read_bytes()
        for p in sorted(root.rglob("*"))
        if p.is_file()
    }


def test_dry_run_upgrade_tier2_collision_previews_companion_writes_nothing(tmp_path, capsys):
    """A dry-run upgrade over an adopter-edited file previews the
    `companion`/tier-2 line (with the `-> *.upstream` target), exits 0, and
    leaves the tree + state byte-identical with no companion on disk."""
    from agentbundle import safety
    from agentbundle.commands.upgrade import _filter_for_primitive
    from agentbundle.render import render_pack

    rc = _install_v1(tmp_path)
    assert rc == 0
    capsys.readouterr()  # drain install output

    skill_paths = [
        rp
        for rp in sorted(_filter_for_primitive(render_pack(PACK_V1), "work-loop", "skills"))
        if (tmp_path / rp).exists()
    ]
    assert skill_paths, "work-loop skill must project at least one file on disk"
    target_rel = skill_paths[0]
    (tmp_path / target_rel).write_bytes(b"# adopter-edited skill body\n")

    before = _snapshot_tree(tmp_path)

    rc = _run_upgrade(
        pack="core",
        catalogue=str(CAT_V2),
        root=str(tmp_path),
        dry_run=True,
    )
    assert rc == 0, "dry-run upgrade must exit 0 even with a Tier-2 collision"

    out = capsys.readouterr().out
    companion_rel = safety.companion_path(Path(target_rel)).as_posix()
    assert "tier-2" in out, f"plan must use the greppable tier-2 label; got:\n{out}"
    assert "companion" in out, f"plan must name the companion action; got:\n{out}"
    assert f"{target_rel} -> {companion_rel}" in out, (
        f"Tier-2 line must show the companion target; got:\n{out}"
    )
    assert "Nothing written." in out, "summary must restate the no-write guarantee"

    # No-write invariant: tree + state byte-identical, no companion on disk.
    assert _snapshot_tree(tmp_path) == before, "dry-run upgrade must write nothing"
    assert not (tmp_path / companion_rel).exists(), "dry-run must not drop the .upstream companion"


def test_dry_run_upgrade_no_edits_previews_overwrite_writes_nothing(tmp_path, capsys):
    """A dry-run upgrade with no adopter edits lists the projected files
    with `overwrite`/tier-1 labels and target paths, exits 0, writes nothing."""
    rc = _install_v1(tmp_path)
    assert rc == 0
    capsys.readouterr()

    before = _snapshot_tree(tmp_path)

    rc = _run_upgrade(
        pack="core",
        catalogue=str(CAT_V2),
        root=str(tmp_path),
        dry_run=True,
    )
    assert rc == 0

    out = capsys.readouterr().out
    assert "overwrite" in out, f"unedited files must preview as overwrite; got:\n{out}"
    assert "tier-1" in out, f"plan must use the greppable tier-1 label; got:\n{out}"
    # A real projected path appears in the plan (the "where").
    state = __import__("agentbundle.config", fromlist=["load_state"]).load_state(
        tmp_path / ".agentbundle-state.toml"
    )
    a_path = sorted(state.row("core", "claude-code").files)[0]
    assert a_path in out, f"plan must show the target path {a_path!r}; got:\n{out}"

    assert _snapshot_tree(tmp_path) == before, "dry-run upgrade must write nothing"


def test_dry_run_upgrade_per_primitive_scopes_to_that_primitive(tmp_path, capsys):
    """`--dry-run --skill work-loop` previews only that skill's files;
    `--dry-run --skill bogus` still exits non-zero (primitive-not-found)."""
    from agentbundle.commands.upgrade import _filter_for_primitive
    from agentbundle.render import render_pack

    rc = _install_v1(tmp_path)
    assert rc == 0
    capsys.readouterr()

    before = _snapshot_tree(tmp_path)

    rc = _run_upgrade(
        pack="core",
        catalogue=str(CAT_V2),
        root=str(tmp_path),
        skill="work-loop",
        dry_run=True,
    )
    assert rc == 0
    out = capsys.readouterr().out

    skill_files = set(_filter_for_primitive(render_pack(PACK_V2), "work-loop", "skills"))
    assert skill_files, "fixture must project a work-loop skill"
    for rp in skill_files:
        assert rp in out, f"per-primitive plan must list {rp!r}; got:\n{out}"
    # A non-skill file (the reviewer agent) must NOT appear.
    agent_files = set(_filter_for_primitive(render_pack(PACK_V2), "reviewer", "agents"))
    for rp in agent_files:
        assert rp not in out, f"per-primitive plan must exclude {rp!r}; got:\n{out}"

    assert _snapshot_tree(tmp_path) == before, "dry-run must write nothing"

    # Primitive-not-found passes through as a non-zero pre-render refusal.
    rc = _run_upgrade(
        pack="core",
        catalogue=str(CAT_V2),
        root=str(tmp_path),
        skill="bogus",
        dry_run=True,
    )
    assert rc != 0, "a --dry-run for a missing primitive must still exit non-zero"
    assert _snapshot_tree(tmp_path) == before


def test_format_plan_line_shape():
    """The shared formatter renders the documented action/tier/path shape,
    and appends the `-> companion` suffix only for a Tier-2 line."""
    from agentbundle.commands._common import (
        format_plan_line,
        plan_action,
        summarize_plan,
    )
    from agentbundle.safety import Tier

    create = format_plan_line("create", "tier-1", ".claude/agents/foo.md")
    assert create.split() == ["create", "tier-1", ".claude/agents/foo.md"]
    assert "->" not in create

    comp = format_plan_line("companion", "tier-2", "AGENTS.md", "AGENTS.upstream.md")
    assert comp.startswith("companion")
    assert "tier-2" in comp
    assert comp.endswith("AGENTS.md -> AGENTS.upstream.md")

    # Action mapping is shared and mirrors a real run's write decision.
    assert plan_action(Tier.TIER_2, on_disk=True) == "companion"
    assert plan_action(Tier.TIER_1, on_disk=True) == "overwrite"
    assert plan_action(Tier.TIER_1, on_disk=False) == "create"

    summary = summarize_plan(["create", "create", "companion"])
    assert "2 create" in summary and "1 companion" in summary
    assert summary.endswith("Nothing written.")


def test_dry_run_upgrade_preflight_path_jail_passthrough(tmp_path):
    """A path-jail-violating projection under `upgrade --dry-run` is refused
    (non-zero), matching the real run's `write_jailed` refusal, and nothing is
    written outside the root."""
    from unittest import mock

    rc = _install_v1(tmp_path)
    assert rc == 0

    before = _snapshot_tree(tmp_path)
    # The v1 install used the dist-tree shape, so upgrade renders via
    # `render_pack`; patch it to return a projection that escapes the root.
    malicious = {"../../evil_dry_run.txt": b"evil"}
    with mock.patch("agentbundle.render.render_pack", return_value=malicious):
        rc = _run_upgrade(
            pack="core",
            catalogue=str(CAT_V2),
            root=str(tmp_path),
            dry_run=True,
        )
    assert rc != 0, "dry-run must surface the path-jail pre-flight failure"
    assert not (tmp_path / ".." / ".." / "evil_dry_run.txt").resolve().exists(), (
        "the escaping file must not be written even under dry-run"
    )
    assert _snapshot_tree(tmp_path) == before, "nothing may change"


def test_upgrade_prefix_violation_writes_nothing(tmp_path, capsys):
    """Non-dry-run upgrade refuses before writing when a Tier-2 path is outside
    allowed_prefixes — probe-all-before-write behavioral change."""
    from unittest import mock

    from agentbundle import safety
    from agentbundle.config import PackState, State, dump_state

    outside_rel = "outside-prefix/file.md"
    # State indicates per-IDE install: files under .claude/ (not apm/ or claude-plugins/).
    # Also records the outside-prefix path from a hypothetical prior install.
    installed_sha = safety.sha256_bytes(b"original\n")
    s = State()
    s.packs[("core", "claude-code")] = PackState(
        installed_version="0.1.0",
        adapter="claude-code",
        scope="repo",
        primitives=["skill"],
        files={
            ".claude/SKILL.md": {"sha": "a" * 64, "from-pack-version": "0.1.0"},
            outside_rel: {"sha": installed_sha, "from-pack-version": "0.1.0"},
        },
    )
    (tmp_path / ".agentbundle-state.toml").write_text(
        dump_state(s), encoding="utf-8", newline="\n"
    )
    # On-disk: user has edited the outside-prefix file (different from installed sha)
    (tmp_path / "outside-prefix").mkdir()
    (tmp_path / outside_rel).write_bytes(b"user edited\n")

    before = _snapshot_tree(tmp_path)
    new_projection = {outside_rel: b"new pack content\n"}

    with mock.patch(
        "agentbundle.commands.install._render_for_repo_scope",
        return_value=("claude-code", new_projection),
    ):
        rc = _run_upgrade(pack="core", catalogue=str(CAT_V2), root=str(tmp_path))

    assert rc != 0, f"upgrade must exit non-zero on prefix violation; got rc={rc}"
    assert _snapshot_tree(tmp_path) == before, "upgrade must write nothing including companions"
    stderr = capsys.readouterr().err
    assert "not within any declared prefix zone" in stderr, (
        f"pre-flight refusal must appear in stderr; got: {stderr!r}"
    )


# ---------------------------------------------------------------------------
# Derive-version + confirmation flow (upgrade-derive-version-confirm spec)
# ---------------------------------------------------------------------------


def test_derives_target_version_from_catalogue(tmp_path, capsys):
    """With no version argument, the target is derived from the
    catalogue's pack.toml and the recap names both versions."""
    from agentbundle.config import load_state

    assert _install_v1(tmp_path) == 0
    capsys.readouterr()  # drop install output

    rc = _run_upgrade(pack="core", catalogue=str(CAT_V2), root=str(tmp_path))
    assert rc == 0
    state = load_state(tmp_path / ".agentbundle-state.toml")
    assert state.row("core", "claude-code").installed_version == "0.2.0"
    recap = capsys.readouterr().out.strip().splitlines()[-1]
    assert recap == "upgraded: core @ repo 0.1.0 -> 0.2.0", recap


def test_per_primitive_recap_shows_from_to(tmp_path, capsys):
    """Per-primitive recap shows from -> to, with `from` the recorded
    primitive override (here installed_version, no prior override)."""
    assert _install_v1(tmp_path) == 0
    capsys.readouterr()

    rc = _run_upgrade(pack="core", catalogue=str(CAT_V2), root=str(tmp_path), skill="work-loop")
    assert rc == 0
    recap = capsys.readouterr().out.strip().splitlines()[-1]
    assert recap == "upgraded: core skill/work-loop @ repo 0.1.0 -> 0.2.0", recap


def test_confirmation_accept_proceeds(tmp_path, capsys, monkeypatch):
    """An interactive `y` reply proceeds with the upgrade."""
    from agentbundle.config import load_state

    assert _install_v1(tmp_path) == 0
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    monkeypatch.setattr("builtins.input", lambda prompt="": "  YES ")

    rc = _run_upgrade(pack="core", catalogue=str(CAT_V2), root=str(tmp_path), yes=False)
    assert rc == 0
    state = load_state(tmp_path / ".agentbundle-state.toml")
    assert state.row("core", "claude-code").installed_version == "0.2.0"


def test_confirmation_decline_writes_nothing(tmp_path, capsys, monkeypatch):
    """A non-affirmative reply aborts non-zero and writes nothing."""
    from agentbundle.config import load_state

    assert _install_v1(tmp_path) == 0
    before = _snapshot_tree(tmp_path)
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    monkeypatch.setattr("builtins.input", lambda prompt="": "n")

    rc = _run_upgrade(pack="core", catalogue=str(CAT_V2), root=str(tmp_path), yes=False)
    assert rc != 0
    assert "aborted; no changes made" in capsys.readouterr().err
    state = load_state(tmp_path / ".agentbundle-state.toml")
    assert state.row("core", "claude-code").installed_version == "0.1.0"
    assert _snapshot_tree(tmp_path) == before


def test_confirmation_eof_treated_as_decline(tmp_path, capsys, monkeypatch):
    """An EOFError at the prompt is treated as a decline."""
    from agentbundle.config import load_state

    assert _install_v1(tmp_path) == 0
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)

    def _raise(prompt=""):
        raise EOFError

    monkeypatch.setattr("builtins.input", _raise)
    rc = _run_upgrade(pack="core", catalogue=str(CAT_V2), root=str(tmp_path), yes=False)
    assert rc != 0
    state = load_state(tmp_path / ".agentbundle-state.toml")
    assert state.row("core", "claude-code").installed_version == "0.1.0"


def test_yes_skips_prompt(tmp_path, monkeypatch):
    """--yes proceeds without reading stdin."""
    from agentbundle.config import load_state

    assert _install_v1(tmp_path) == 0

    def _boom(prompt=""):
        raise AssertionError("input() must not be called with --yes")

    monkeypatch.setattr("builtins.input", _boom)
    rc = _run_upgrade(pack="core", catalogue=str(CAT_V2), root=str(tmp_path), yes=True)
    assert rc == 0
    state = load_state(tmp_path / ".agentbundle-state.toml")
    assert state.row("core", "claude-code").installed_version == "0.2.0"


def test_non_tty_without_yes_refuses(tmp_path, capsys, monkeypatch):
    """Non-TTY stdin without --yes refuses and never blocks on input()."""
    from agentbundle.config import load_state

    assert _install_v1(tmp_path) == 0
    monkeypatch.setattr("sys.stdin.isatty", lambda: False)

    def _boom(prompt=""):
        raise AssertionError("input() must not be called when stdin is not a TTY")

    monkeypatch.setattr("builtins.input", _boom)
    rc = _run_upgrade(pack="core", catalogue=str(CAT_V2), root=str(tmp_path), yes=False)
    assert rc != 0
    assert "--yes" in capsys.readouterr().err
    state = load_state(tmp_path / ".agentbundle-state.toml")
    assert state.row("core", "claude-code").installed_version == "0.1.0"


def test_dry_run_no_prompt_no_write(tmp_path, capsys, monkeypatch):
    """--dry-run resolves the version, prompts nothing, writes nothing —
    even on a non-TTY without --yes (the refusal is short-circuited)."""
    assert _install_v1(tmp_path) == 0
    before = _snapshot_tree(tmp_path)
    monkeypatch.setattr("sys.stdin.isatty", lambda: False)

    def _boom(prompt=""):
        raise AssertionError("input() must not be called under --dry-run")

    monkeypatch.setattr("builtins.input", _boom)
    rc = _run_upgrade(
        pack="core",
        catalogue=str(CAT_V2),
        root=str(tmp_path),
        dry_run=True,
        yes=False,
    )
    assert rc == 0
    assert _snapshot_tree(tmp_path) == before


@pytest.mark.parametrize(
    "pack_toml_body",
    [
        '[pack]\nname = "core"\ndescription = "no version"\nseeds = []\n',  # missing key
        '[pack]\nname = "core"\nversion = 2\nseeds = []\n',  # non-string
        "[other]\nx = 1\n",  # no [pack] table
    ],
    ids=["missing-key", "non-string", "no-pack-table"],
)
def test_missing_pack_version_errors(tmp_path, capsys, pack_toml_body):
    """A resolved catalogue whose pack.toml declares no usable [pack]
    version (missing key, non-string, or no [pack] table) exits non-zero with
    the catalogue-pointing message — the new derive check, not the spec-version
    gate (which doesn't read [pack] version)."""
    assert _install_v1(tmp_path) == 0

    cat = tmp_path / "noversion_cat"
    pack_dir = cat / "packs" / "core"
    pack_dir.mkdir(parents=True)
    (pack_dir / "pack.toml").write_text(pack_toml_body, encoding="utf-8", newline="\n")
    rc = _run_upgrade(pack="core", catalogue=str(cat), root=str(tmp_path))
    assert rc != 0
    assert "declares no [pack] version" in capsys.readouterr().err


def test_per_primitive_from_uses_recorded_override(tmp_path, capsys):
    """On a second per-primitive upgrade, `from` is the recorded primitive
    override (0.2.0), not installed_version (0.1.0)."""
    assert _install_v1(tmp_path) == 0
    # First per-primitive upgrade → records skill/work-loop @ 0.2.0.
    assert (
        _run_upgrade(pack="core", catalogue=str(CAT_V2), root=str(tmp_path), skill="work-loop")
        == 0
    )
    capsys.readouterr()
    # Second per-primitive upgrade → from is the recorded override 0.2.0.
    assert (
        _run_upgrade(pack="core", catalogue=str(CAT_V3), root=str(tmp_path), skill="work-loop")
        == 0
    )
    recap = capsys.readouterr().out.strip().splitlines()[-1]
    assert recap == "upgraded: core skill/work-loop @ repo 0.2.0 -> 0.3.0", recap


def test_already_current_states_so_with_yes(tmp_path, capsys):
    """Upgrading to the version already installed states 'already at'
    and re-applies (with --yes)."""
    # Install 0.2.0, then "upgrade" against the same 0.2.0 catalogue.
    assert _run_install("core", str(CAT_V2), str(tmp_path)) == 0
    capsys.readouterr()

    rc = _run_upgrade(pack="core", catalogue=str(CAT_V2), root=str(tmp_path), yes=True)
    assert rc == 0
    captured = capsys.readouterr()
    assert "is already at 0.2.0" in captured.err
    # Clean re-apply (no local edits) → the upfront drift notice is suppressed
    # (install-state-visibility zero-suppression).
    assert "have local edits" not in captured.err
    recap = captured.out.strip().splitlines()[-1]
    # A same-version re-apply is no longer mislabelled `upgraded: X -> X`
    # A clean re-apply (no local edits) reads
    # `re-applied: … (already current)`.
    assert recap == "re-applied: core @ repo 0.2.0 (already current)", recap


def test_reapply_with_local_edit_notice_and_companion_recap(tmp_path, capsys):
    """Re-applying at the same version after a local edit prints the
    upfront drift notice (before the action) and a recap that names the edited
    file kept as a companion — never `upgraded: X -> X`."""
    from agentbundle.config import load_state

    assert _run_install("core", str(CAT_V2), str(tmp_path)) == 0
    capsys.readouterr()

    # Edit one installed file so it drifts (becomes Tier-2).
    state = load_state(tmp_path / ".agentbundle-state.toml")
    ps = state.row("core", "claude-code")
    edited_relpath = sorted(ps.files)[0]
    (tmp_path / edited_relpath).write_text("# local edit\n", encoding="utf-8", newline="\n")

    rc = _run_upgrade(pack="core", catalogue=str(CAT_V2), root=str(tmp_path), yes=True)
    assert rc == 0
    captured = capsys.readouterr()
    # Upfront notice on stderr, before the action.
    assert "installed file(s) have local edits" in captured.err
    # Recap names the companion count and stays a re-apply, not an upgrade.
    recap = captured.out.strip().splitlines()[-1]
    assert recap.startswith("re-applied: core @ repo 0.2.0 —")
    assert "kept as .upstream companions" in recap
    assert "->" not in recap


def test_per_primitive_upgrade_suppresses_whole_pack_drift_notice(tmp_path, capsys):
    """Carve-out: a per-primitive upgrade re-applies only that primitive's
    files, so the whole-pack drift notice is deliberately NOT printed — even
    when other installed files have local edits."""
    from agentbundle.config import load_state

    assert _install_v1(tmp_path) == 0
    # Edit an installed file so a whole-pack run *would* notice drift.
    state = load_state(tmp_path / ".agentbundle-state.toml")
    ps = state.row("core", "claude-code")
    (tmp_path / sorted(ps.files)[0]).write_text("# local edit\n", encoding="utf-8", newline="\n")
    capsys.readouterr()

    rc = _run_upgrade(pack="core", catalogue=str(CAT_V2), root=str(tmp_path), skill="work-loop")
    assert rc == 0
    assert "have local edits" not in capsys.readouterr().err


def test_already_current_interactive_offers_reapply(tmp_path, capsys, monkeypatch):
    """Interactively, the already-current prompt offers to re-apply."""
    assert _run_install("core", str(CAT_V2), str(tmp_path)) == 0
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    seen = {}

    def _capture(prompt=""):
        seen["prompt"] = prompt
        return "y"

    monkeypatch.setattr("builtins.input", _capture)
    rc = _run_upgrade(pack="core", catalogue=str(CAT_V2), root=str(tmp_path), yes=False)
    assert rc == 0
    assert "already at 0.2.0" in seen["prompt"]
    assert "Re-apply" in seen["prompt"]
    # Prompt half: the old "repairs local drift" jargon is gone, and the
    # prompt states edits are preserved as companions. (Both assertions fail
    # against the pre-change wording, so they actually pin the rewrite.)
    assert "repairs local drift" not in seen["prompt"]
    assert ".upstream companions" in seen["prompt"]
