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
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from agentbundle.commands.render import run

# The test fixture pack lives next to the build tests; it has both .sh and .py hooks.
# File: packages/agentbundle/tests/unit/test_render_cmd.py
#   parents[0] = packages/agentbundle/tests/unit
#   parents[1] = packages/agentbundle/tests
#   parents[2] = packages/agentbundle
#   parents[3] = packages
#   parents[4] = repo root
FIXTURE_PACKS = (
    Path(__file__).resolve().parents[2]
    / "agentbundle"
    / "build"
    / "tests"
    / "fixtures"
    / "packs"
)
FIXTURE_CORE = FIXTURE_PACKS / "core"

# The real repo packs/core — used for F-build parity gate.
REPO_ROOT = Path(__file__).resolve().parents[4]
REAL_CORE = REPO_ROOT / "packs" / "core"


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

    # skill — projects as a directory under .claude/skills/
    assert any(".claude/skills/" in k for k in tree), \
        f"no skill in tree; keys={sorted(tree)}"
    # agent — projects as .claude/agents/<name>.md
    assert any(".claude/agents/" in k and k.endswith(".md") for k in tree), \
        f"no agent in tree; keys={sorted(tree)}"
    # hook-body — projects as tools/hooks/<name>.{sh,py}
    assert any("tools/hooks/" in k for k in tree), \
        f"no hook-body in tree; keys={sorted(tree)}"
    # hook-wiring — projects as .claude/settings.local.json
    assert any("settings.local.json" in k for k in tree), \
        f"no hook-wiring in tree; keys={sorted(tree)}"
    # command — projects as .claude/commands/<name>.md
    assert any(".claude/commands/" in k and k.endswith(".md") for k in tree), \
        f"no command in tree; keys={sorted(tree)}"


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
    # Fixture core has baz.sh in .apm/hooks/; expect tools/hooks/baz.sh
    sh_keys = [k for k in tree if k.endswith(".sh") and "hooks" in k]
    assert sh_keys, f"no .sh hook in tree; hook-related keys={[k for k in tree if 'hook' in k]}"


def test_hook_extension_preservation_py(tmp_path):
    """.py hooks project as .py (not renamed)."""
    out_dir = tmp_path / "out"
    args = _args(pack_path=str(FIXTURE_CORE), output=str(out_dir))
    rc = run(args)
    assert rc == 0

    tree = _tree(out_dir)
    # Fixture core has baz.py in .apm/hooks/; expect tools/hooks/baz.py
    py_keys = [k for k in tree if k.endswith(".py") and "hooks" in k]
    assert py_keys, f"no .py hook in tree; hook-related keys={[k for k in tree if 'hook' in k]}"


# ---------------------------------------------------------------------------
# Test 4: F-build parity gate (goal-based)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(
    not REAL_CORE.exists(),
    reason="packs/core not present — skipping F-build parity gate",
)
def test_render_byte_identical_to_make_build(tmp_path):
    """agentbundle render packs/core --output <tmp> is byte-identical to
    `make build PACK=core OUTPUT_DIR=<tmp2>` (excluding marketplace.json which
    `make build` aggregates across all packs but `render` only sees core).

    Pattern mirrors test_render_pack_to_dir_byte_identical_to_make_build in
    tests/unit/test_render.py.
    """
    via_render = tmp_path / "via-render"
    args = _args(pack_path=str(REAL_CORE), output=str(via_render))
    rc = run(args)
    assert rc == 0, "render command returned non-zero"

    via_make = tmp_path / "via-make"
    via_make.mkdir()
    proc = subprocess.run(
        [
            "make",
            "-C",
            str(REPO_ROOT),
            "build",
            f"OUTPUT_DIR={via_make}",
            "PACK=core",
        ],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, f"make build failed: {proc.stderr}"

    def _drop_marketplace(d: dict) -> dict:
        return {k: v for k, v in d.items() if "marketplace.json" not in k}

    render_tree = _drop_marketplace(_tree(via_render))
    make_tree = _drop_marketplace(_tree(via_make))

    # `make build` runs over all packs; restrict to core's subtrees.
    make_core_tree = {
        k: v
        for k, v in make_tree.items()
        if "/core/" in k or k.endswith("/core")
    }
    render_core_tree = {
        k: v
        for k, v in render_tree.items()
        if "/core/" in k or k.endswith("/core")
    }

    assert render_core_tree == make_core_tree, (
        "render output differs from make build for core pack.\n"
        f"only in render: {sorted(set(render_core_tree) - set(make_core_tree))}\n"
        f"only in make:   {sorted(set(make_core_tree) - set(render_core_tree))}"
    )


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


# ---------------------------------------------------------------------------
# Test 7: Path-jail — malicious --output that itself escapes
# ---------------------------------------------------------------------------


def test_render_path_jail_on_malicious_output(tmp_path, capsys):
    """A user-provided --output that resolves to a parent path is jailed.

    The relevant invariant: every write goes through `write_jailed(output_dir, ...)`
    which calls `assert_under(root, target)`. If we pass a relpath that tries
    to escape (e.g. `../../escape`), write_jailed raises PathJailError and the
    command exits non-zero.

    We simulate this by monkey-patching `render_pack` to return a relpath that
    contains a `..` escape, ensuring the jail fires even if the pack itself is
    clean.
    """
    import agentbundle.commands.render as render_cmd

    out_dir = tmp_path / "sub"
    out_dir.mkdir()

    # Patch render.render_pack to return a malicious relpath.
    original_render_pack = render_cmd._render.render_pack

    def _malicious_render_pack(pack_path, **kwargs):
        # Return a relpath that would escape out_dir if not jailed.
        return {"../../escape/evil.txt": b"evil content"}

    render_cmd._render.render_pack = _malicious_render_pack
    try:
        args = _args(pack_path=str(FIXTURE_CORE), output=str(out_dir))
        rc = run(args)
    finally:
        render_cmd._render.render_pack = original_render_pack

    assert rc != 0
    captured = capsys.readouterr()
    assert "refusing to write outside" in captured.err, \
        f"expected jail refusal in stderr, got: {captured.err!r}"
    # Verify the evil file was not created.
    assert not (tmp_path.parent / "escape" / "evil.txt").exists()
