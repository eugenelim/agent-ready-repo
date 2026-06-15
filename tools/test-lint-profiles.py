#!/usr/bin/env python3
"""Self-test for tools/lint-profiles.py (pack-profiles AC9, T2).

Pure-stdlib Python so the suite runs on Windows without an MSYS shell.
Pattern: build a fixture tree (profiles/ + packs/) in a tempdir, run the linter
via subprocess against it (`--root <tmp>`), and assert exit code + substrings —
real-invocation, not synthesised import.

Trees:
  A — happy: solution-architect (user, no deps) + full-ceremony (repo, core
      first, governance-extras requires core ^0.1 satisfied by core v0.4.9).
      Exit 0.
  B — scope mismatch: a user profile naming a repo-only pack. Exit 1.
  C — dependency-incomplete: full-ceremony with core removed. Exit 1.
  D — mis-ordered: governance-extras before its dep core. Exit 1.
  E — dependency version mismatch: dep present but at an unsatisfying version.
      Exit 1.
  F — unknown pack: a profile naming a pack not in packs/. Exit 1.
  G — no profiles/ dir: nothing to lint. Exit 0.
"""

from __future__ import annotations

import pathlib
import subprocess
import sys
import tempfile

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
LINTER = REPO_ROOT / "tools" / "lint-profiles.py"


def fail(label: str, msg: str, output: str = "") -> None:
    print(f"✖ {label}: {msg}", file=sys.stderr)
    if output:
        print("---", file=sys.stderr)
        print(output, file=sys.stderr)
        print("---", file=sys.stderr)
    sys.exit(1)


def run_linter(root: pathlib.Path) -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, str(LINTER), "--root", str(root)],
        capture_output=True,
        text=True,
    )
    return proc.returncode, proc.stdout + proc.stderr


def _pack(packs_dir: pathlib.Path, name: str, version: str,
          allowed_scopes: list[str], required: list[tuple[str, str]]) -> None:
    pdir = packs_dir / name
    pdir.mkdir(parents=True, exist_ok=True)
    lines = [
        "[pack]",
        f'name = "{name}"',
        f'version = "{version}"',
        'adapter-contract = { version = "0.6" }',
        "[pack.install]",
        f'default-scope = "{allowed_scopes[0]}"',
        "allowed-scopes = [" + ", ".join(f'"{s}"' for s in allowed_scopes) + "]",
    ]
    for dep_name, dep_range in required:
        lines += [
            "[[pack.dependencies.required]]",
            'catalogue = "agent-ready-repo"',
            f'pack = "{dep_name}"',
            f'version = "{dep_range}"',
        ]
    (pdir / "pack.toml").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _profile(root: pathlib.Path, name: str, scope: str, packs: list[str]) -> None:
    pdir = root / "profiles"
    pdir.mkdir(parents=True, exist_ok=True)
    body = [f'scope = "{scope}"', 'description = "fixture"']
    for p in packs:
        body += ["[[packs]]", f'pack = "{p}"']
    (pdir / f"{name}.toml").write_text("\n".join(body) + "\n", encoding="utf-8")


def _standard_packs(root: pathlib.Path) -> None:
    packs = root / "packs"
    # user-scope, dual-allowed, no deps
    for n in ("architect", "research", "contracts"):
        _pack(packs, n, "0.3.0", ["user", "repo"], [])
    # repo-scope governance packs
    _pack(packs, "core", "0.4.9", ["repo"], [])
    _pack(packs, "governance-extras", "0.1.2", ["repo"], [("core", "^0.1")])
    _pack(packs, "monorepo-extras", "0.1.2", ["repo"], [("core", "^0.1")])


def main() -> int:
    # Tree A — happy.
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)
        _standard_packs(root)
        _profile(root, "solution-architect", "user", ["architect", "research", "contracts"])
        _profile(root, "full-ceremony", "repo", ["core", "governance-extras", "monorepo-extras"])
        code, out = run_linter(root)
        if code != 0:
            fail("A/happy", f"expected exit 0, got {code}", out)
        if "OK" not in out:
            fail("A/happy", "expected an OK summary", out)

    # Tree B — scope mismatch (user profile naming repo-only core).
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)
        _standard_packs(root)
        _profile(root, "bad-scope", "user", ["architect", "core"])
        code, out = run_linter(root)
        if code != 1:
            fail("B/scope", f"expected exit 1, got {code}", out)
        if "does not allow scope 'user'" not in out:
            fail("B/scope", "expected scope-homogeneity violation", out)

    # Tree C — dependency-incomplete (governance-extras without core).
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)
        _standard_packs(root)
        _profile(root, "no-core", "repo", ["governance-extras"])
        code, out = run_linter(root)
        if code != 1:
            fail("C/incomplete", f"expected exit 1, got {code}", out)
        if "dependency-incomplete" not in out:
            fail("C/incomplete", "expected dependency-incomplete violation", out)

    # Tree D — mis-ordered (governance-extras before core).
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)
        _standard_packs(root)
        _profile(root, "misordered", "repo", ["governance-extras", "core"])
        code, out = run_linter(root)
        if code != 1:
            fail("D/order", f"expected exit 1, got {code}", out)
        if "mis-ordered" not in out:
            fail("D/order", "expected mis-ordered violation", out)

    # Tree E — dep present but version unsatisfying.
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)
        packs = root / "packs"
        _pack(packs, "core", "0.4.9", ["repo"], [])
        _pack(packs, "needs-v2", "0.1.0", ["repo"], [("core", "^2.0")])
        _profile(root, "bad-version", "repo", ["core", "needs-v2"])
        code, out = run_linter(root)
        if code != 1:
            fail("E/version", f"expected exit 1, got {code}", out)
        if "does not satisfy it" not in out:
            fail("E/version", "expected version-mismatch violation", out)

    # Tree F — unknown pack.
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)
        _standard_packs(root)
        _profile(root, "ghost", "repo", ["core", "does-not-exist"])
        code, out = run_linter(root)
        if code != 1:
            fail("F/unknown", f"expected exit 1, got {code}", out)
        if "not found in packs/" not in out:
            fail("F/unknown", "expected unknown-pack violation", out)

    # Tree G — no profiles/ dir.
    with tempfile.TemporaryDirectory() as d:
        root = pathlib.Path(d)
        _standard_packs(root)
        code, out = run_linter(root)
        if code != 0:
            fail("G/empty", f"expected exit 0, got {code}", out)

    print("✓ test-lint-profiles: all trees pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
