#!/usr/bin/env python3
"""Self-test for tools/lint-design-craft-agnostic.py.

Pure-stdlib Python so the suite runs on Windows without an MSYS shell.
Pattern (mirrors test-lint-knowledge-surface-parity.py): write fixture
Markdown into a tempdir, point DESIGN_CRAFT_ROOT at it, run the linter as a
subprocess, and assert the exit code (and a diagnostic substring on the
failure cases).

The clean case is load-bearing: it carries the tokens that look stack-shaped
but are legitimate agnostic *method* — the adjective "angular", an all-letter
`#facade` heading anchor, the word "gap", a "grid of cards" concept, the
"reduced-motion" principle, an "80% of users" percentage, "the 1990s", and
"ease of use" — and must still pass. A regex that fails this case is
over-broad and would block honest prose.
"""

from __future__ import annotations

import os
import pathlib
import subprocess
import sys
import tempfile

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
LINTER = REPO_ROOT / "tools" / "lint-design-craft-agnostic.py"

_FAILURES: list[str] = []
_CASES = 0

CLEAN = """# Direction

The brand wants **angular**, geometric forms — not soft ones. We react to
the vibe and name the goals. Mind the gap between density and clarity; a grid
of cards orients the eye. Motion communicates state, and we honor
reduced-motion for ease of use. Point to WCAG for the contrast floor. Around
80% of users scan first; the 1990s taught us that. A 16:9 hero reads wide.

See [the facade pattern](#facade) and [states](#handle-all-states).
"""


def _run(root: pathlib.Path) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["DESIGN_CRAFT_ROOT"] = str(root)
    return subprocess.run(
        [sys.executable, str(LINTER)],
        capture_output=True, text=True, env=env, check=False,
    )


def _check(name: str, root: pathlib.Path, want_code: int, want_sub: str = "") -> None:
    global _CASES
    _CASES += 1
    res = _run(root)
    out = res.stdout + res.stderr
    if res.returncode != want_code:
        _FAILURES.append(
            f"{name}: exit {res.returncode}, want {want_code}\n  output: {out!r}"
        )
        return
    if want_sub and want_sub not in out:
        _FAILURES.append(f"{name}: missing {want_sub!r} in output\n  output: {out!r}")


def _write(tmp: pathlib.Path, body: str) -> pathlib.Path:
    d = tmp / "fixture"
    d.mkdir(parents=True, exist_ok=True)
    (d / "SKILL.md").write_text(body, encoding="utf-8")
    return d


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td)

        # Clean: tricky-but-legal tokens must pass.
        _check("clean", _write(tmp / "a", CLEAN), 0)

        # One failure case per rule category.
        dirty = {
            "framework": "Build this in React with hooks.",
            "css": "Wrap it in a `@media (min-width: ...)` query.",
            "aria": 'Add `role="navigation"` to the landmark.',
            "animation-lib": "Animate it with Framer Motion.",
            "hex": "The primary is #1a2b3c on the surface.",
            "hex-greyscale": "Use #fff on #ccc for the muted row.",
            "rgb-hsl": "The accent is rgb(26, 43, 60), hover hsl(210, 40%, 30%).",
            "dimension": "Set the base spacing to 16px and the duration to 200ms.",
            "dimension-units": "The hero is 100vh tall with 12pt captions.",
            "duration-seconds": "Let the transition run for 0.2s.",
            "ratio": "Text must clear a 4.5:1 contrast ratio.",
            "easing": "Use cubic-bezier(0.4, 0, 0.2, 1) for the curve.",
        }
        for i, (name, body) in enumerate(dirty.items()):
            _check(name, _write(tmp / f"d{i}", body), 1, "::error::")

        # Missing scan root is a tool error, not a traceback.
        _check("missing-root", tmp / "does-not-exist", 2, "does not exist")

    if _FAILURES:
        print(f"✖ {len(_FAILURES)}/{_CASES} cases failed:")
        for f in _FAILURES:
            print(f"  - {f}")
        return 1
    print(f"✓ all {_CASES} cases passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
