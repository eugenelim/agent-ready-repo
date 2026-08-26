"""T3: `agentbundle render` subcommand tests.

Coverage:
  1. Happy-path: render packs/core → expected file tree covering all five
     primitive types (skill, agent, hook-body, hook-wiring, command).
  2. Hook extension preservation: .sh projects as .sh, .py projects as .py.
  3. F-build parity (goal-based): render_pack_to_dir vs make build for core pack.
  4. Path-jail: malicious relpath attempt is refused with non-zero exit.
  5. Missing pack.toml: non-zero exit with descriptive stderr.
  6. Unknown target: non-zero exit with descriptive stderr.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from agentbundle import render
from agentbundle.commands.render import run

# The test fixture pack lives next to the build tests; it has both .sh and .py hooks.
# File: packages/agentbundle/tests/unit/test_render_cmd.py
#   parents[0] = packages/agentbundle/tests/unit
#   parents[1] = packages/agentbundle/tests
#   parents[2] = packages/agentbundle
#   parents[3] = packages
FIXTURE_PACKS = (
    Path(__file__).resolve().parents[2]
    / "tests"
    / "build_pipeline"
    / "fixtures"
    / "packs"
)
FIXTURE_CORE = FIXTURE_PACKS / "core"


def _args(**kwargs) -> argparse.Namespace:
    """Build a Namespace that mimics what argparse produces for `render`."""
    defaults = {"pack_path": str(FIXTURE_CORE), "output": None, "target": None}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


# ---------------------------------------------------------------------------
# Helper: walk a directory into a dict[relpath -> bytes]
# ---------------------------------------------------------------------------


def _tree(root: Path) -> dict[str, bytes]:
    out: dict[str, bytes] = {}
    for p in sorted(root.rglob("*")):
        if p.is_file():
            out[p.relative_to(root).as_posix()] = p.read_bytes()
    return out


# ---------------------------------------------------------------------------
# Test 1: Happy path — file tree covers all five primitive types
# ---------------------------------------------------------------------------


def test_render_produces_expected_primitives_for_fixture_core(tmp_path):
    """Render the fixture core pack and assert all five primitives appear."""
    out_dir = tmp_path / "out"
    args = _args(pack_path=str(FIXTURE_CORE), output=str(out_dir))

    rc = run(args)
    assert rc == 0

    tree = _tree(out_dir)
    assert tree, "output tree is empty"

    # skill — on the claude-plugins route components land at the PLUGIN ROOT
    # (`claude-plugins/<pack>/skills/`), because Claude Code plugins load
    # skills/, agents/ and commands/ from there. `render` runs that recipe, so
    # its output moved with it; the repo/user `.claude/` routes did not.
    assert any("claude-plugins/core/skills/" in k for k in tree), \
        f"no skill in tree; keys={sorted(tree)}"
    # agent — projects as <plugin root>/agents/<name>.md
    assert any("claude-plugins/core/agents/" in k and k.endswith(".md") for k in tree), \
        f"no agent in tree; keys={sorted(tree)}"
    # hook-body — projects at the plugin root as hooks/<name>.{sh,py}
    assert any("claude-plugins/core/hooks/" in k for k in tree), \
        f"no hook-body in tree; keys={sorted(tree)}"
    # hook-wiring is compiled into plugin.json, not projected as settings.
    assert not any("settings.local.json" in k for k in tree), tree
    # command — projects as <plugin root>/commands/<name>.md
    assert any("claude-plugins/core/commands/" in k and k.endswith(".md") for k in tree), \
        f"no command in tree; keys={sorted(tree)}"
    assert not any("claude-plugins/core/.claude/" in k for k in tree), tree


# ---------------------------------------------------------------------------
# Test 2: stdout lists files written, one per line
# ---------------------------------------------------------------------------


def test_render_prints_relative_paths_to_stdout(tmp_path, capsys):
    """One line per written file on stdout."""
    out_dir = tmp_path / "out"
    args = _args(pack_path=str(FIXTURE_CORE), output=str(out_dir))

    rc = run(args)
    assert rc == 0

    captured = capsys.readouterr()
    printed = [line for line in captured.out.splitlines() if line]
    assert printed, "nothing printed to stdout"

    # Every printed relpath must exist on disk.
    for relpath in printed:
        assert (out_dir / relpath).exists(), f"{relpath!r} printed but not on disk"


# ---------------------------------------------------------------------------
# Test 3: Hook extension preservation
# ---------------------------------------------------------------------------


def test_hook_extension_preservation_sh(tmp_path):
    """.sh hooks project as .sh (not renamed)."""
    out_dir = tmp_path / "out"
    args = _args(pack_path=str(FIXTURE_CORE), output=str(out_dir))
    rc = run(args)
    assert rc == 0

    tree = _tree(out_dir)
    # Fixture core has baz.sh in .apm/hooks/; expect plugin-root hooks/baz.sh
    sh_keys = [k for k in tree if k.endswith(".sh") and "hooks" in k]
    assert sh_keys, f"no .sh hook in tree; hook-related keys={[k for k in tree if 'hook' in k]}"


def test_hook_extension_preservation_py(tmp_path):
    """.py hooks project as .py (not renamed)."""
    out_dir = tmp_path / "out"
    args = _args(pack_path=str(FIXTURE_CORE), output=str(out_dir))
    rc = run(args)
    assert rc == 0

    tree = _tree(out_dir)
    # Fixture core has baz.py in .apm/hooks/; expect plugin-root hooks/baz.py
    py_keys = [k for k in tree if k.endswith(".py") and "hooks" in k]
    assert py_keys, f"no .py hook in tree; hook-related keys={[k for k in tree if 'hook' in k]}"


# ---------------------------------------------------------------------------
# Test 4: command/library parity gate
# ---------------------------------------------------------------------------


def test_render_command_matches_library_bytes(tmp_path):
    """The command writes the same fixture bytes as the library API."""
    via_render = tmp_path / "via-render"
    args = _args(pack_path=str(FIXTURE_CORE), output=str(via_render))
    rc = run(args)
    assert rc == 0, "render command returned non-zero"
    assert _tree(via_render) == render.render_pack(FIXTURE_CORE)


def test_render_command_preserves_executable_mode(
    tmp_path, monkeypatch
):
    """The mode-aware render surface must survive the jailed command write."""
    import agentbundle.commands.render as render_cmd

    monkeypatch.setattr(
        render_cmd._render,
        "render_pack_files",
        lambda pack_path, **kwargs: {
            "agent-plugins/portable/skills/example/run.sh": render.RenderedFile(
                b"#!/bin/sh\n", 0o755
            )
        },
    )
    out_dir = tmp_path / "out"

    assert run(_args(output=str(out_dir))) == 0
    assert (
        out_dir
        / "agent-plugins"
        / "portable"
        / "skills"
        / "example"
        / "run.sh"
    ).stat().st_mode & 0o111


# ---------------------------------------------------------------------------
# Test 5: Missing pack.toml → non-zero exit
# ---------------------------------------------------------------------------


def test_render_missing_pack_toml_exits_nonzero(tmp_path, capsys):
    no_pack = tmp_path / "no-pack"
    no_pack.mkdir()
    out_dir = tmp_path / "out"
    args = _args(pack_path=str(no_pack), output=str(out_dir))

    rc = run(args)
    assert rc != 0
    captured = capsys.readouterr()
    assert "pack.toml" in captured.err.lower(), \
        f"expected 'pack.toml' in stderr, got: {captured.err!r}"


# ---------------------------------------------------------------------------
# Test 6: Unknown --target → non-zero exit
# ---------------------------------------------------------------------------


def test_render_unknown_target_exits_nonzero(tmp_path, capsys):
    out_dir = tmp_path / "out"
    args = _args(pack_path=str(FIXTURE_CORE), output=str(out_dir), target="bogus-adapter")

    rc = run(args)
    assert rc != 0
    captured = capsys.readouterr()
    assert "bogus-adapter" in captured.err or "unknown target" in captured.err.lower(), \
        f"expected target name or 'unknown target' in stderr, got: {captured.err!r}"


def test_render_claude_target_selects_only_claude_distribution_route(tmp_path):
    """An explicit Claude target must not also emit the adapter-less APM route."""
    out_dir = tmp_path / "out"
    rc = run(
        _args(
            pack_path=str(FIXTURE_CORE),
            output=str(out_dir),
            target="claude-code",
        )
    )

    assert rc == 0
    tree = _tree(out_dir)
    assert any(path.startswith("claude-plugins/core/") for path in tree)
    assert not any(path.startswith("apm/") for path in tree)


def test_render_non_claude_adapter_does_not_emit_distribution_routes(tmp_path):
    """A direct-install adapter target must not inherit an unrelated package route."""
    out_dir = tmp_path / "out"
    rc = run(
        _args(
            pack_path=str(FIXTURE_CORE),
            output=str(out_dir),
            target="codex",
        )
    )

    assert rc == 0
    assert _tree(out_dir) == {}


# ---------------------------------------------------------------------------
# Test 7: Path-jail — malicious --output that itself escapes
# ---------------------------------------------------------------------------


def test_render_path_jail_on_malicious_output(tmp_path, capsys):
    """A user-provided --output that resolves to a parent path is jailed.

    The relevant invariant: every write goes through `write_jailed(output_dir, ...)`
    which calls `assert_under(root, target)`. If we pass a relpath that tries
    to escape (e.g. `../../escape`), write_jailed raises PathJailError and the
    command exits non-zero.

    We simulate this by monkey-patching `render_pack_files` to return a relpath that
    contains a `..` escape, ensuring the jail fires even if the pack itself is
    clean.
    """
    import agentbundle.commands.render as render_cmd

    out_dir = tmp_path / "sub"
    out_dir.mkdir()

    # Patch render.render_pack_files to return a malicious relpath.
    original_render_pack = render_cmd._render.render_pack_files

    def _malicious_render_pack(pack_path, **kwargs):
        # Return a relpath that would escape out_dir if not jailed.
        return {
            "../../escape/evil.txt": render.RenderedFile(b"evil content", 0o644)
        }

    render_cmd._render.render_pack_files = _malicious_render_pack
    try:
        args = _args(pack_path=str(FIXTURE_CORE), output=str(out_dir))
        rc = run(args)
    finally:
        render_cmd._render.render_pack_files = original_render_pack

    assert rc != 0
    captured = capsys.readouterr()
    assert "refusing to write outside" in captured.err, \
        f"expected jail refusal in stderr, got: {captured.err!r}"
    # Verify the evil file was not created.
    assert not (tmp_path.parent / "escape" / "evil.txt").exists()
