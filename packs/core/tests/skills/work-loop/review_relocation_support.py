"""Fixtures for the `review-artifact.py` command tests.

Generic report files the adjudication commands read, plus helpers that load a
script by path under a unique name and run its `main` in-process. Only the
standard library is used, and the module loads scripts by path under unique
names so a bare `import` never binds the wrong sibling.
"""

from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import sys
from pathlib import Path
from types import ModuleType

SENTINEL = "Clean — ready to commit."


def fingerprint(location: str, line: int, title: str) -> str:
    """Re-derive a finding fingerprint the way the skill documents it."""
    return hashlib.sha256(f"{location}|{line}|{title}".encode()).hexdigest()


FP_A = fingerprint("src/example.py", 10, "**1. Missing guard**")
FP_B = fingerprint("src/other.py", 20, "**1. Unchecked input**")
FP_OLD = "d" * 40  # the 40-hex SHA-1 form a pre-2.3.0 run may still hold

_FINDING_A = "**1. Missing guard** `src/example.py:10`"
_FINDING_B = "**1. Unchecked input** `src/other.py:20`"
_SUSTAINED_A = f"{_FINDING_A}. The handler skips validation. Fix: validate the input."
_SUSTAINED_B = f"{_FINDING_B}. The loader trusts its caller. Fix: check the caller."


def _envelope(main: str, indeterminate: str = "None.") -> str:
    """Build the three-section finding-adjudicator envelope."""
    return (
        f"## Main-loop result\n{main}\n\n## Refuted audit\n\nNone.\n\n"
        f"## Indeterminate audit\n\n{indeterminate}\n"
    )


FILES: dict[str, str] = {
    "adj-clean.md": _envelope(SENTINEL),
    "adj-findings-a.md": _envelope(_SUSTAINED_A),
    "adj-findings-b.md": _envelope(_SUSTAINED_B),
    "adj-indeterminate.md": _envelope(
        SENTINEL, "ADJUDICATION-INDETERMINATE: the claim cannot be decided."
    ),
    "adj-bad-shape.md": _envelope("Everything looks fine."),
    "legacy-findings-a.md": _FINDING_A + "\n",
    "legacy-clean.md": f"Review complete.\n\n{SENTINEL}\n",
    "legacy-ship-it.md": "Review complete.\nSHIP IT\n",
    "raw-clean.md": SENTINEL + "\n",
    "raw-footer.md": f"{SENTINEL}\n\n## Not checked\n- Did not run the slow suite.\n",
    "raw-findings.md": _FINDING_A + "\n",
    "raw-noise.md": "Looks fine to me.\n",
    "exact-sentinel.txt": SENTINEL,
    "wrong-sentinel.txt": SENTINEL + "\n",
}


def load_script(name: str, path: Path) -> ModuleType:
    """Load one script by path under a unique name."""
    spec = importlib.util.spec_from_file_location(name, str(path))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module  # a `@dataclass` resolves its module by name
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(name, None)
    return module


def call_main(module: ModuleType, argv: list[str]) -> tuple[int, str, str]:
    """Run `module.main(argv)` in-process; return (exit code, stdout, stderr).

    The streams are real text wrappers, not `StringIO`: a script that loads a
    sibling reconfigures `sys.stdout` while importing it, and `StringIO` has no
    `reconfigure`.
    """
    out_bytes, err_bytes = io.BytesIO(), io.BytesIO()
    out = io.TextIOWrapper(out_bytes, encoding="utf-8", newline="")
    err = io.TextIOWrapper(err_bytes, encoding="utf-8", newline="")
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = module.main(argv)
        except SystemExit as exc:
            code = exc.code if isinstance(exc.code, int) else 1
    out.flush()
    err.flush()
    return (
        int(code or 0),
        out_bytes.getvalue().decode("utf-8"),
        err_bytes.getvalue().decode("utf-8"),
    )
