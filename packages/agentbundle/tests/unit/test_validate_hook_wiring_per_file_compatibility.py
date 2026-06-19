"""T2 tests: validate.py rails 4c/4d swallow hook-wiring compat refusals.

Verification mode: TDD.
Spec: docs/specs/incompatible-hook-event-drop AC1–AC5, AC6b.
Plan: docs/specs/incompatible-hook-event-drop/plan.md § T2.

Ten cases:
  1.  test_validate_packs_core_exits_zero               AC1 + AC2 (load-bearing)
  2.  test_validate_swallows_missing_attach_to_agent     AC1 + swallow (omitted field)
  3.  test_validate_refuses_on_empty_attach_to_agent_string  AC4b (empty string = unknown)
  4.  test_validate_still_refuses_on_hook_wiring_symlink      AC3
  5.  test_validate_still_refuses_on_toml_parse_failure       AC4
  6.  test_validate_still_refuses_on_unknown_agent_reference  AC4b (load-bearing)
  7.  test_validate_still_refuses_on_allowed_adapters_violation  AC5 (scoping)
  8.  test_validate_info_text_uses_pinned_wording_one_file_one_reason  AC2
  9.  test_validate_info_text_uses_pinned_wording_one_file_two_reasons AC2
  10. test_validate_info_text_uses_pinned_wording_two_files             AC2
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_HERE = Path(__file__).resolve().parent
# packs/ lives four levels above the unit-test directory:
#   packages/agentbundle/tests/unit → packages/agentbundle/tests → ...
_PACKS_DIR = _HERE.parent.parent.parent.parent / "packs"

_PACK_TOML_V08_REPO = """\
[pack]
name = "{name}"
version = "0.1.0"
description = "Fixture pack for hook-wiring compat tests."

[pack.adapter-contract]
version = "0.8"

[pack.install]
default-scope = "repo"
allowed-scopes = ["repo"]
"""


def _args(pack_path: Path) -> argparse.Namespace:
    ns = argparse.Namespace()
    ns.pack_path = str(pack_path)
    ns.strict = False
    return ns


def _run(pack_path: Path):
    """Invoke validate.run and return (rc, stdout, stderr) via capsys-compatible
    call. Uses validate_mod.run directly; caller captures with capsys."""
    from agentbundle.commands import validate as validate_mod

    return validate_mod.run(_args(pack_path))


def _make_hook_wiring_pack(
    root: Path,
    *,
    name: str = "fixture-pack",
    wiring_files: dict[str, str],
    agent_files: list[str] | None = None,
) -> Path:
    """Build a minimal v0.8 pack with hook-wiring entries.

    Args:
        root:          tmp_path base directory.
        name:          Pack name used in pack.toml.
        wiring_files:  Mapping of ``<stem>.toml`` filename → TOML content.
        agent_files:   List of agent stem names (creates ``<name>.md`` files).
    """
    pack = root / name
    pack.mkdir(parents=True, exist_ok=True)
    (pack / "pack.toml").write_text(
        _PACK_TOML_V08_REPO.format(name=name), encoding="utf-8"
    )
    wiring_dir = pack / ".apm" / "hook-wiring"
    wiring_dir.mkdir(parents=True, exist_ok=True)
    for fname, content in wiring_files.items():
        (wiring_dir / fname).write_text(content, encoding="utf-8")
    agents_dir = pack / ".apm" / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)
    for stem in (agent_files or []):
        (agents_dir / f"{stem}.md").write_text(f"# {stem}\n", encoding="utf-8")
    return pack


# ---------------------------------------------------------------------------
# Test 1: packs/core exits zero (load-bearing AC1 + AC2 pin)
# ---------------------------------------------------------------------------


def test_validate_packs_core_exits_zero(capsys):
    """AC1: agentbundle validate packs/core exits 0 with the two-reason
    info line on stdout and no 'validate:' refusal on stderr.

    session-start.toml fires BOTH reasons (vocabulary + attach-to-agent)
    because it uses SessionStart (not in kiro's vocab) AND has no
    attach-to-agent field.
    """
    core_path = _PACKS_DIR / "core"
    if not core_path.exists():
        pytest.skip("packs/core not available in this test environment")

    rc = _run(core_path)
    captured = capsys.readouterr()

    assert rc == 0, f"Expected exit 0, got {rc}. stderr: {captured.err!r}"
    assert "validate:" not in captured.err, (
        f"Unexpected 'validate:' refusal on stderr: {captured.err!r}"
    )
    # AC2: two-reason form because both core hook-wirings (session-start.toml
    # and work-loop-check.toml) lack attach-to-agent AND use an out-of-vocab
    # PascalCase event for kiro.
    expected_info = (
        "info: pack core: the following hook-wiring file(s) will not project to kiro "
        "(event not in adapter vocabulary + kiro requires 'attach-to-agent'): "
        "hook-wiring/session-start.toml, and hook-wiring/work-loop-check.toml."
    )
    assert expected_info in captured.out, (
        f"Expected info line not found in stdout.\n"
        f"Expected: {expected_info!r}\n"
        f"Got stdout: {captured.out!r}"
    )


# ---------------------------------------------------------------------------
# Test 2: Swallow missing attach-to-agent (omitted field, event IN vocab)
# ---------------------------------------------------------------------------


def test_validate_swallows_missing_attach_to_agent(tmp_path, capsys):
    """Swallow: hook-wiring that omits attach-to-agent AND uses a vocab
    event exits 0; stdout contains info: line with reason
    'kiro requires 'attach-to-agent''.
    """
    pack = _make_hook_wiring_pack(
        tmp_path,
        name="missing-attach",
        wiring_files={
            # agentSpawn is IN kiro's vocabulary; no attach-to-agent field
            "on-spawn.toml": "[[hooks.agentSpawn]]\ncommand = \"echo hi\"\n",
        },
        agent_files=["my-agent"],
    )
    rc = _run(pack)
    captured = capsys.readouterr()

    assert rc == 0, f"Expected exit 0, got {rc}. stderr: {captured.err!r}"
    assert "validate:" not in captured.err, (
        f"Unexpected refusal: {captured.err!r}"
    )
    assert "info:" in captured.out, (
        f"Expected info: line on stdout, got: {captured.out!r}"
    )
    assert "kiro requires 'attach-to-agent'" in captured.out, (
        f"Expected attach-to-agent reason in stdout, got: {captured.out!r}"
    )


# ---------------------------------------------------------------------------
# Test 3: Refuse empty attach-to-agent string (round-3 reconciliation pin)
# ---------------------------------------------------------------------------


def test_validate_refuses_on_empty_attach_to_agent_string(tmp_path, capsys):
    """AC4b: attach-to-agent = \"\" is treated as unknown-agent and refuses
    with exit 1. Empty string is not in agent_basenames (\"\" not in set)."""
    pack = _make_hook_wiring_pack(
        tmp_path,
        name="empty-attach",
        wiring_files={
            "on-spawn.toml": (
                "attach-to-agent = \"\"\n"
                "[[hooks.agentSpawn]]\ncommand = \"echo hi\"\n"
            ),
        },
        agent_files=["my-agent"],
    )
    rc = _run(pack)
    captured = capsys.readouterr()

    assert rc == 1, f"Expected exit 1, got {rc}"
    assert "or names an unknown agent" in captured.err, (
        f"Expected 'or names an unknown agent' in stderr, got: {captured.err!r}"
    )


# ---------------------------------------------------------------------------
# Test 4: Refuse on hook-wiring symlink (AC3)
# ---------------------------------------------------------------------------


def test_validate_still_refuses_on_hook_wiring_symlink(tmp_path, capsys):
    """AC3: a symlink under .apm/hook-wiring/ causes exit 1 with the
    security refusal 'pack <name>'s hook-wiring entry is a symlink'."""
    pack = _make_hook_wiring_pack(
        tmp_path,
        name="symlink-wiring",
        wiring_files={},
        agent_files=["my-agent"],
    )
    # Create a symlink instead of a regular file in hook-wiring/
    wiring_dir = pack / ".apm" / "hook-wiring"
    target = tmp_path / "real_file.toml"
    target.write_text("[[hooks.agentSpawn]]\ncommand = \"x\"\n", encoding="utf-8")
    (wiring_dir / "sym.toml").symlink_to(target)

    rc = _run(pack)
    captured = capsys.readouterr()

    assert rc == 1, f"Expected exit 1, got {rc}"
    assert "hook-wiring entry is a symlink" in captured.err, (
        f"Expected symlink refusal in stderr, got: {captured.err!r}"
    )


# ---------------------------------------------------------------------------
# Test 5: Refuse on TOML parse failure (AC4)
# ---------------------------------------------------------------------------


def test_validate_still_refuses_on_toml_parse_failure(tmp_path, capsys):
    """AC4: a malformed hook-wiring TOML causes exit 1 with
    'failed to parse' in stderr."""
    pack = _make_hook_wiring_pack(
        tmp_path,
        name="bad-toml",
        wiring_files={
            "broken.toml": "this is not valid TOML = = =\n",
        },
        agent_files=["my-agent"],
    )
    rc = _run(pack)
    captured = capsys.readouterr()

    assert rc == 1, f"Expected exit 1, got {rc}"
    assert "failed to parse" in captured.err, (
        f"Expected 'failed to parse' in stderr, got: {captured.err!r}"
    )


# ---------------------------------------------------------------------------
# Test 6: Refuse on unknown-agent reference (load-bearing AC4b)
# ---------------------------------------------------------------------------


def test_validate_still_refuses_on_unknown_agent_reference(tmp_path, capsys):
    """AC4b: attach-to-agent = 'ghost-agent' with no matching agents/ghost-agent.md
    exits 1 with 'or names an unknown agent' in stderr."""
    pack = _make_hook_wiring_pack(
        tmp_path,
        name="unknown-agent",
        wiring_files={
            "on-spawn.toml": (
                "attach-to-agent = \"ghost-agent\"\n"
                "[[hooks.agentSpawn]]\ncommand = \"echo hi\"\n"
            ),
        },
        # Only my-agent.md is present; ghost-agent.md is NOT
        agent_files=["my-agent"],
    )
    rc = _run(pack)
    captured = capsys.readouterr()

    assert rc == 1, f"Expected exit 1, got {rc}"
    assert "or names an unknown agent" in captured.err, (
        f"Expected 'or names an unknown agent' in stderr, got: {captured.err!r}"
    )


# ---------------------------------------------------------------------------
# Test 7: Refuse on allowed-adapters violation (AC5 scoping pin)
# ---------------------------------------------------------------------------


def test_validate_still_refuses_on_allowed_adapters_violation(tmp_path, capsys):
    """AC5: a schema cross-field violation (bad allowed-adapters) exits 1.
    Pins that the hook-wiring compat swallow doesn't bleed to unrelated rails."""
    pack = tmp_path / "bad-adapter"
    pack.mkdir(parents=True, exist_ok=True)
    # Pack with an unrecognised adapter in allowed-adapters — this trips
    # the _validate_allowed_adapters rail (4a territory).
    (pack / "pack.toml").write_text(
        '[pack]\n'
        'name = "bad-adapter"\n'
        'version = "0.1.0"\n'
        'description = "Fixture."\n\n'
        '[pack.adapter-contract]\n'
        'version = "0.8"\n\n'
        '[pack.install]\n'
        'default-scope = "repo"\n'
        'allowed-scopes = ["repo"]\n'
        'allowed-adapters = ["totally-unknown-adapter-xyz"]\n',
        encoding="utf-8",
    )
    rc = _run(pack)
    captured = capsys.readouterr()

    assert rc == 1, f"Expected exit 1, got {rc}. stderr: {captured.err!r}"


# ---------------------------------------------------------------------------
# Test 8: Pinned wording — one file, one reason
# ---------------------------------------------------------------------------


def test_validate_info_text_uses_pinned_wording_one_file_one_reason(tmp_path, capsys):
    """AC2: validate stdout matches the pinned one-file-one-reason form.

    Uses a wiring with an out-of-vocab event AND a present+known agent
    (so only vocabulary fires, not attach-to-agent).
    """
    pack = _make_hook_wiring_pack(
        tmp_path,
        name="one-reason-pack",
        wiring_files={
            # SessionStart is NOT in kiro's vocabulary; attach-to-agent IS present
            "session-start.toml": (
                "attach-to-agent = \"my-agent\"\n"
                "[[hooks.SessionStart]]\nhooks = [{type = \"command\", command = \"x\"}]\n"
            ),
        },
        agent_files=["my-agent"],
    )
    rc = _run(pack)
    captured = capsys.readouterr()

    assert rc == 0, f"Expected exit 0, got {rc}. stderr: {captured.err!r}"
    expected = (
        "info: pack one-reason-pack: the following hook-wiring file(s) will not "
        "project to kiro (event not in adapter vocabulary): hook-wiring/session-start.toml."
    )
    assert expected in captured.out, (
        f"Pinned wording mismatch.\nExpected: {expected!r}\nGot stdout: {captured.out!r}"
    )


# ---------------------------------------------------------------------------
# Test 9: Pinned wording — one file, two reasons
# ---------------------------------------------------------------------------


def test_validate_info_text_uses_pinned_wording_one_file_two_reasons(tmp_path, capsys):
    """AC2: validate stdout matches the pinned two-reason form.

    One wiring file trips BOTH vocabulary AND attach-to-agent rails.
    """
    pack = _make_hook_wiring_pack(
        tmp_path,
        name="two-reason-pack",
        wiring_files={
            # SessionStart not in vocab AND no attach-to-agent field
            "session-start.toml": (
                "[[hooks.SessionStart]]\nhooks = [{type = \"command\", command = \"x\"}]\n"
            ),
        },
        agent_files=["my-agent"],
    )
    rc = _run(pack)
    captured = capsys.readouterr()

    assert rc == 0, f"Expected exit 0, got {rc}. stderr: {captured.err!r}"
    expected = (
        "info: pack two-reason-pack: the following hook-wiring file(s) will not "
        "project to kiro (event not in adapter vocabulary + kiro requires "
        "'attach-to-agent'): hook-wiring/session-start.toml."
    )
    assert expected in captured.out, (
        f"Pinned wording mismatch.\nExpected: {expected!r}\nGot stdout: {captured.out!r}"
    )


# ---------------------------------------------------------------------------
# Test 10: Pinned wording — two files, one reason each
# ---------------------------------------------------------------------------


def test_validate_info_text_uses_pinned_wording_two_files(tmp_path, capsys):
    """AC2: validate stdout matches the pinned two-file form with
    serial-comma-plus-'and' and lexicographic ordering."""
    pack = _make_hook_wiring_pack(
        tmp_path,
        name="two-file-pack",
        wiring_files={
            # Both use out-of-vocab events; both have attach-to-agent
            "alpha.toml": (
                "attach-to-agent = \"my-agent\"\n"
                "[[hooks.SessionStart]]\nhooks = [{type = \"command\", command = \"x\"}]\n"
            ),
            "beta.toml": (
                "attach-to-agent = \"my-agent\"\n"
                "[[hooks.SessionStart]]\nhooks = [{type = \"command\", command = \"y\"}]\n"
            ),
        },
        agent_files=["my-agent"],
    )
    rc = _run(pack)
    captured = capsys.readouterr()

    assert rc == 0, f"Expected exit 0, got {rc}. stderr: {captured.err!r}"
    expected = (
        "info: pack two-file-pack: the following hook-wiring file(s) will not "
        "project to kiro (event not in adapter vocabulary): "
        "hook-wiring/alpha.toml, and hook-wiring/beta.toml."
    )
    assert expected in captured.out, (
        f"Pinned wording mismatch.\nExpected: {expected!r}\nGot stdout: {captured.out!r}"
    )
