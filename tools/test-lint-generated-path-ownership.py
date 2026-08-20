#!/usr/bin/env python3
"""Subprocess fixtures for lint-generated-path-ownership.py."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from collections.abc import Callable
from contextlib import contextmanager
from pathlib import Path

LINT = Path(__file__).with_name("lint-generated-path-ownership.py")


def _write(path: Path, content: str = "") -> None:
    """Create a UTF-8 fixture file, including its parent directories."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _recipe(root: Path, packs: list[str]) -> None:
    """Write the minimal self-host recipe used by every fixture."""
    quoted = ", ".join(repr(pack) for pack in packs)
    _write(
        root / "packages/agentbundle/agentbundle/build/recipes/self-host.toml",
        "[recipe.packs]\ninclude = [" + quoted + "]\n\n"
        "[recipe.adapters]\ntargets = [\"claude-code\"]\n",
    )


def _contract(root: Path, primitive: str = "skill", target: str = ".claude/skills/") -> None:
    """Write one directory projection, enough to isolate each behavior."""
    _write(
        root / "contracts/adapter.toml",
        "[adapter.claude-code]\n\n[[adapter.claude-code.projection]]\n"
        f"primitive = {primitive!r}\nmode = \"copy\"\ntarget-path = {target!r}\n",
    )


def _skill(root: Path, pack: str, name: str) -> None:
    """Add a directory-valued skill producer."""
    _write(root / f"packs/{pack}/.apm/skills/{name}/SKILL.md", "---\nname: test\n---\n")


def _projected_skill(root: Path, name: str) -> None:
    """Add the projected form of a skill producer."""
    _write(root / f".claude/skills/{name}/SKILL.md", "projected\n")


@contextmanager
def fixture() -> Path:
    """Yield one independent clean fixture; callers never mutate a shared tree."""
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        _recipe(root, ["alpha"])
        _contract(root)
        _skill(root, "alpha", "one")
        _projected_skill(root, "one")
        yield root


def _run(root: Path) -> subprocess.CompletedProcess[str]:
    """Invoke the real lint exactly as CI fixtures need to invoke it."""
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        [sys.executable, "-B", "-I", str(LINT), "--root", str(root)],
        text=True, capture_output=True, check=False, env=environment,
    )


def _expect(result: subprocess.CompletedProcess[str], code: int, text: str) -> None:
    """Assert both CI status and a diagnostic fragment."""
    assert result.returncode == code, (result.returncode, result.stdout, result.stderr)
    assert text in result.stdout + result.stderr, (text, result.stdout, result.stderr)


def clean_fixture() -> None:
    with fixture() as root:
        _expect(_run(root), 0, "passed")


def orphan_skill() -> None:
    with fixture() as root:
        _write(root / ".claude/skills/extra/SKILL.md", "orphan\n")
        _expect(_run(root), 1, ".claude/skills/extra")


def missing_skill() -> None:
    with fixture() as root:
        (root / ".claude/skills/one/SKILL.md").unlink()
        (root / ".claude/skills/one").rmdir()
        _expect(_run(root), 1, "missing projection: .claude/skills/one")


def ambiguous_skill_owner() -> None:
    with fixture() as root:
        _recipe(root, ["alpha", "beta"])
        _skill(root, "alpha", "dup")
        _skill(root, "beta", "dup")
        _write(root / ".claude/skills/dup/SKILL.md", "projected\n")
        _expect(_run(root), 1, "ambiguous ownership for 'skill' 'dup'")


def seed_collision_different_content() -> None:
    with fixture() as root:
        _write(root / "packs/alpha/seeds/shared/file.txt", "alpha\n")
        _write(root / "packs/beta/seeds/shared/file.txt", "beta\n")
        _expect(_run(root), 1, "seed collision at 'shared/file.txt'")


def seed_collision_identical_content() -> None:
    with fixture() as root:
        _write(root / "packs/alpha/seeds/shared/file.txt", "same\n")
        _write(root / "packs/beta/seeds/shared/file.txt", "same\n")
        _expect(_run(root), 1, "seed collision at 'shared/file.txt'")


def agent_stem_match() -> None:
    with fixture() as root:
        _contract(root, primitive="agent", target=".claude/agents/")
        _write(root / "packs/alpha/.apm/agents/x.md", "source\n")
        _write(root / ".claude/agents/x.toml", "projected\n")
        _expect(_run(root), 0, "passed")


def empty_recipe_include() -> None:
    with fixture() as root:
        _recipe(root, [])
        _expect(_run(root), 1, "vacuously")


def zero_roots() -> None:
    with fixture() as root:
        _write(root / "contracts/adapter.toml", "[adapter.claude-code]\n")
        _expect(_run(root), 1, "vacuously")


def absent_recipe() -> None:
    with fixture() as root:
        (root / "packages/agentbundle/agentbundle/build/recipes/self-host.toml").unlink()
        _expect(_run(root), 1, "vacuously")


def fixture_exemption_does_not_fire() -> None:
    with fixture() as root:
        _expect(_run(root), 0, "passed")


def symlinked_seed_directory() -> None:
    """A pack whose `seeds/` is itself a symlink to a directory.

    A symlink to a directory satisfies `is_dir()`, so a guard that walks after
    that check descends the link's target and finds no symlinked *children* —
    the link it should have refused is the walk's own root. This case pins the
    base check; walking children alone leaves it green.
    """
    with fixture() as root:
        _write(root / "outside" / "file.txt", "planted\n")
        (root / "packs" / "alpha").mkdir(parents=True, exist_ok=True)
        (root / "packs" / "alpha" / "seeds").symlink_to(root / "outside")
        _expect(_run(root), 1, "refusing to scan around it")


def symlink_in_generated_root() -> None:
    """A symlinked entry inside a generated root.

    Ownership would otherwise be claimed by a path this audit does not follow.
    """
    with fixture() as root:
        _write(root / "outside" / "SKILL.md", "planted\n")
        (root / ".claude" / "skills").mkdir(parents=True, exist_ok=True)
        (root / ".claude" / "skills" / "linked").symlink_to(root / "outside")
        _expect(_run(root), 1, "symlink in a generated")


CASES: list[tuple[str, Callable[[], None]]] = [
    ("clean fixture", clean_fixture),
    ("orphan skill", orphan_skill),
    ("missing skill", missing_skill),
    ("ambiguous skill owner", ambiguous_skill_owner),
    ("seed collision with different content", seed_collision_different_content),
    ("seed collision with identical content", seed_collision_identical_content),
    ("agent stem match", agent_stem_match),
    ("empty recipe include", empty_recipe_include),
    ("zero generated roots", zero_roots),
    ("absent recipe", absent_recipe),
    ("fixture exemption does not fire", fixture_exemption_does_not_fire),
    ("symlinked seed directory", symlinked_seed_directory),
    ("symlink in a generated root", symlink_in_generated_root),
]


def main() -> int:
    """Run every case and identify the first failure without a test framework."""
    for name, case in CASES:
        try:
            case()
        except (AssertionError, OSError, subprocess.SubprocessError) as exc:
            print(f"FAIL: {name}: {exc}", file=sys.stderr)
            return 1
    print(f"ok — {len(CASES)} cases passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
