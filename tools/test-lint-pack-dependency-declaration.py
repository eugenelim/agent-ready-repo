#!/usr/bin/env python3
"""Subprocess fixtures for lint-pack-dependency-declaration.py."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path

LINT = Path(__file__).with_name("lint-pack-dependency-declaration.py")


def write(path: Path, content: str = "") -> None:
    """Create a UTF-8 fixture file, including its parent directories."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def pack(root: Path, name: str, dependencies: tuple[tuple[str, str], ...] = ()) -> Path:
    """Create one fixture manifest, with dependency kind and target name."""
    lines = ["[pack]", f'name = "{name}"']
    for kind, target in dependencies:
        lines.extend([
            "",
            f"[[pack.dependencies.{kind}]]",
            'catalogue = "test"',
            f'pack = "{target}"',
            'version = "*"',
        ])
    directory = root / "packs" / name
    write(directory / "pack.toml", "\n".join(lines) + "\n")
    return directory


def skill(root: Path, pack_name: str, primitive: str, content: str = "") -> None:
    """Create an owned skill primitive, optionally with source content."""
    write(
        root / "packs" / pack_name / ".apm" / "skills" / primitive / "SKILL.md",
        content,
    )


def run_case(
    name: str,
    build: Callable[[Path], None],
    expected_code: int,
    *expected_text: str,
) -> None:
    """Run one isolated fixture and assert its status and diagnostic text."""
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        build(root)
        environment = dict(os.environ)
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        proc = subprocess.run(
            [sys.executable, "-B", "-I", str(LINT), "--root", str(root)],
            capture_output=True,
            text=True,
            env=environment,
            check=False,
        )
        output = proc.stdout + proc.stderr
        if proc.returncode != expected_code:
            raise AssertionError(
                f"{name}: expected exit {expected_code}, got {proc.returncode}:\n"
                f"{output}"
            )
        for text in expected_text:
            if text not in output:
                raise AssertionError(f"{name}: missing {text!r}:\n{output}")


def used_required(root: Path) -> None:
    pack(root, "a", (("required", "b"),))
    pack(root, "b")
    skill(root, "b", "b-prim")
    write(root / "packs" / "a" / "use.md", "Use b-prim.\n")


def undeclared_path(root: Path) -> None:
    pack(root, "a")
    pack(root, "b")
    skill(root, "a", "a-prim")
    skill(root, "b", "b-prim")
    write(root / "packs" / "a" / "code.py", 'PATH = "packs/b/.apm/skills/b-prim/"\n')


def declared_path(root: Path) -> None:
    pack(root, "a", (("required", "b"),))
    pack(root, "b")
    skill(root, "a", "a-prim")
    skill(root, "b", "b-prim")
    write(
        root / "packs" / "a" / "code.py",
        'PATH = "packs/b/.apm/skills/b-prim/"\nUSE = "b-prim"\n',
    )


def comment_path(root: Path) -> None:
    pack(root, "a")
    pack(root, "b")
    skill(root, "a", "a-prim")
    skill(root, "b", "b-prim")
    write(root / "packs" / "a" / "code.py", "# packs/b/.apm/skills/b-prim/\n")


def hash_inside_string_path(root: Path) -> None:
    """A real cross-pack reference preceded by a `#` inside a string literal.

    Splitting the line on the first `#` truncates the reference and lets the
    undeclared dependency pass. `comment_path` cannot catch that regression,
    because there the `#` really does start a comment and both readings agree.
    """
    pack(root, "a")
    pack(root, "b")
    skill(root, "a", "a-prim")
    skill(root, "b", "b-prim")
    write(
        root / "packs" / "a" / "code.py",
        'SEP = "#"\nTARGET = "packs/b/.apm/skills/b-prim/"\n',
    )


def markdown_path(root: Path) -> None:
    pack(root, "a")
    pack(root, "b")
    skill(root, "a", "a-prim", "packs/b/.apm/skills/b-prim/\n")
    skill(root, "b", "b-prim")


def test_path(root: Path) -> None:
    pack(root, "a")
    pack(root, "b")
    skill(root, "a", "a-prim")
    skill(root, "b", "b-prim")
    write(root / "packs" / "a" / "tests" / "probe.py", '"packs/b/x"\n')


def dead_required(root: Path) -> None:
    pack(root, "a", (("required", "b"),))
    pack(root, "b")
    skill(root, "b", "b-prim")


def dead_required_eponymous_pack(root: Path) -> None:
    """A dead declaration whose target pack is named after a primitive it owns.

    Pack `b` owns a primitive also called `b`, so `a`'s manifest line
    `pack = "b"` is itself a textual reference to one of `b`'s primitives. If the
    usage scan reads `pack.toml`, the declaration satisfies itself and this dead
    entry passes. `dead_required` cannot catch that, because its primitive is
    named `b-prim` and the manifest never spells it.
    """
    pack(root, "a", (("required", "b"),))
    pack(root, "b")
    skill(root, "b", "b")


def dead_recommended(root: Path) -> None:
    pack(root, "a", (("recommended", "b"),))
    pack(root, "b")
    skill(root, "b", "b-prim")


def conflict_only(root: Path) -> None:
    pack(root, "a", (("conflicts", "b"),))
    pack(root, "b")
    skill(root, "b", "b-prim")


def hyphen_boundary(root: Path) -> None:
    pack(root, "a", (("required", "b"),))
    pack(root, "b")
    skill(root, "b", "new-spec")
    write(root / "packs" / "a" / "note.md", "spec\n")


def duplicate_primitive(root: Path) -> None:
    pack(root, "a")
    pack(root, "b")
    skill(root, "a", "dup")
    skill(root, "b", "dup")


def no_primitives(root: Path) -> None:
    pack(root, "a")


def symlinked_directory_in_pack(root: Path) -> None:
    """A cross-pack reference reachable only through a symlinked directory.

    The walk declines to descend a directory symlink, so the reference below is
    invisible. Refusing the link is the only way the scan stays honest about
    what it inspected.
    """
    pack(root, "a")
    pack(root, "b")
    skill(root, "a", "a-prim")
    skill(root, "b", "b-prim")
    write(root / "outside" / "code.py", 'T = "packs/b/.apm/skills/b-prim/"\n')
    (root / "packs" / "a" / "linked").symlink_to(root / "outside")


def main() -> int:
    """Execute all fixtures, each in a fresh temporary directory."""
    cases: tuple[tuple[str, Callable[[Path], None], int, tuple[str, ...]], ...] = (
        ("used required dependency", used_required, 0, ("passed",)),
        ("undeclared executable path", undeclared_path, 1,
         ("packs/a/code.py:1", "without declaring `b`")),
        ("declared executable path", declared_path, 0, ("passed",)),
        ("comment-only path", comment_path, 0, ("passed",)),
        ("hash inside a string literal", hash_inside_string_path, 1,
         ("without declaring `b`",)),
        ("symlinked directory in a pack", symlinked_directory_in_pack, 1,
         ("refusing to scan around it",)),
        ("Markdown-only path", markdown_path, 0, ("passed",)),
        ("test-only path", test_path, 0, ("passed",)),
        ("dead required declaration", dead_required, 1,
         ("pack `a` declares `b`",)),
        ("dead declaration for an eponymous pack",
         dead_required_eponymous_pack, 1, ("pack `a` declares `b`",)),
        ("dead recommended declaration", dead_recommended, 1,
         ("pack `a` declares `b`",)),
        ("conflict is not a declaration", conflict_only, 0, ("passed",)),
        ("hyphen boundary", hyphen_boundary, 1,
         ("pack `a` declares `b`",)),
        ("ambiguous primitive ownership", duplicate_primitive, 1,
         ("ambiguous ownership",)),
        ("no packs", lambda _root: None, 1, ("vacuously",)),
        ("no primitives", no_primitives, 1, ("vacuously",)),
    )
    passed = 0
    for name, build, expected_code, expected_text in cases:
        try:
            run_case(name, build, expected_code, *expected_text)
        except AssertionError as exc:
            print(f"FAIL: {exc}", file=sys.stderr)
            return 1
        passed += 1
    print(f"ok — {passed} cases passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
