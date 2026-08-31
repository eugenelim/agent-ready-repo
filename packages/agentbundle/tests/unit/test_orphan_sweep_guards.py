"""AC28: no orphan sweep may delete a projected skill on unreadable state.

Seven call sites. Four previously swallowed the failure into an empty protected
set; three built no protected set at all. Both shapes delete user-installed
content, and both are silent about it.
"""

from __future__ import annotations

import importlib
from pathlib import Path

import pytest
from agentbundle.build.adapters._sweep_guard import (
    OrphanSweepRefused,
    installed_skill_names,
)

SWEEP_ADAPTERS = (
    "claude_code",
    "codex",
    "copilot",
    "kiro",
    "cursor",
    "gemini",
    "kiro_ide",
)
DELEGATING_ADAPTERS = ("claude_code", "codex", "copilot", "kiro")


def _state(root: Path, body: str) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    path = root / ".agentbundle-state.toml"
    path.write_text(body, encoding="utf-8")
    return path


def test_absent_state_yields_an_empty_set(tmp_path: Path):
    # Absent is not a failure: nothing is installed, so nothing is protected.
    target = tmp_path / ".claude" / "skills"
    target.mkdir(parents=True)
    assert installed_skill_names(tmp_path, target, adapter="claude-code") == set()


def test_unreadable_state_refuses_rather_than_protecting_nothing(tmp_path: Path):
    # The two shapes that made this reachable: malformed TOML, and a schema
    # version this build does not recognise. State 0.5 makes the second case
    # ordinary rather than theoretical — a 0.4-pinned reader raises on every
    # file written after the first direct install.
    target = tmp_path / ".claude" / "skills"
    target.mkdir(parents=True)

    for body in ('schema-version = "0.6"\n', "not = [valid toml\n", "packs = 1\n"):
        _state(tmp_path, body)
        with pytest.raises(OrphanSweepRefused) as raised:
            installed_skill_names(tmp_path, target, adapter="claude-code")
        message = str(raised.value)
        assert "refusing to sweep" in message
        assert "delete" in message, "the message must name the consequence"


def test_a_recorded_row_is_protected(tmp_path: Path):
    # The positive control: without it, a guard that always refused would pass
    # every assertion above while protecting nothing.
    target = tmp_path / ".claude" / "skills"
    target.mkdir(parents=True)
    _state(
        tmp_path,
        'schema-version = "0.5"\n'
        '[pack.alpha.adapters.claude-code]\n'
        'installed-version = "0.0.0"\n'
        'scope = "repo"\n'
        'install-route = "cli"\n'
        'user-root = "~/.agentbundle"\n'
        '[pack.alpha.adapters.claude-code.files.".claude/skills/alpha/SKILL.md"]\n'
        'sha = "x"\n',
    )
    assert installed_skill_names(tmp_path, target, adapter="claude-code") == {"alpha"}


@pytest.mark.parametrize("adapter", SWEEP_ADAPTERS)
def test_every_sweep_call_site_consults_the_guard(adapter):
    # One fixture per call site. A sweep that stops calling the guard — by
    # reverting to `except ConfigError: return set()`, or by dropping the
    # union in the three that had no protected set — fails here.
    module = importlib.import_module(f"agentbundle.build.adapters.{adapter}")
    source = Path(module.__file__).read_text(encoding="utf-8")
    assert "_sweep_guard" in source, f"{adapter} does not consult the sweep guard"
    assert "except ConfigError:\n        return set()" not in source, (
        f"{adapter} still swallows an unreadable state file into an empty "
        f"protected set"
    )


@pytest.mark.parametrize("adapter", DELEGATING_ADAPTERS)
def test_the_four_delegate_rather_than_carrying_a_copy(adapter):
    # These four each carried their own copy with a "keep in sync" comment.
    # That arrangement is what let the other three drift into having no
    # protected set at all, so the copies are gone rather than re-synchronised.
    module = importlib.import_module(f"agentbundle.build.adapters.{adapter}")
    source = Path(module.__file__).read_text(encoding="utf-8")
    assert "installed_skill_names" in source
    assert "skill_dir_rel = target_dir.relative_to(output_root)" not in source, (
        f"{adapter} still carries its own copy of the protected-set walk"
    )


@pytest.mark.parametrize("adapter", ("cursor", "gemini", "kiro_ide"))
def test_the_three_now_union_the_installed_set(adapter):
    # These built `expected_names` from pack sources only and never consulted
    # state, so a sweep deleted everything `agentbundle install` had put in the
    # same directory.
    module = importlib.import_module(f"agentbundle.build.adapters.{adapter}")
    source = Path(module.__file__).read_text(encoding="utf-8")
    assert "expected_names |= installed_skill_names(" in source, (
        f"{adapter} sweeps without unioning the installed set"
    )


def test_install_reports_a_sweep_refusal_instead_of_a_traceback(tmp_path: Path, capsys):
    # `install` reaches the sweep through each adapter's single-pack `project()`
    # wrapper, so the refusal arrived as a traceback with internal paths on
    # stderr. The handler that fixes it had no test: removing the try/except
    # restored the traceback with the whole suite green.
    from agentbundle.commands import install as install_cmd

    _state(tmp_path, 'schema-version = "0.6"\n')
    target = tmp_path / ".claude" / "skills" / "installed"
    target.mkdir(parents=True)
    (target / "SKILL.md").write_text("# installed\n", encoding="utf-8")

    class _Args:
        catalogue = None
        output = str(tmp_path)
        pack = "core"
        profile = scope = adapter = skill = None
        all_skills = dry_run = force = yes = False

    try:
        exit_code = install_cmd.run(_Args())
    except Exception as exc:  # noqa: BLE001 - the point is that none escapes
        raise AssertionError(f"a sweep refusal escaped as {type(exc).__name__}") from exc

    # The command may fail earlier for unrelated reasons in this fixture; what
    # must never happen is an unhandled OrphanSweepRefused.
    assert exit_code != 0
    assert "Traceback" not in "".join(capsys.readouterr())
