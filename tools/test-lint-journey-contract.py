#!/usr/bin/env python3
"""Self-test for lint-journey-contract.py.

Uses LJC_JOURNEY_DIR env-override (fixture mode) to run the linter against
controlled fixture trees rather than the real repo.

Exit 0 when all assertions pass; exit 1 on the first failure.
"""

from __future__ import annotations

import os
import pathlib
import subprocess
import sys
import tempfile

_SCRIPT = pathlib.Path(__file__).parent / "lint-journey-contract.py"

_VALID = """\
---
pack: alpha
scope: repo
contract:
  useItWhen: "when x"
  youProvide: "the task"
  youReceive: "an artifact"
  yourDecisions:
    - "Approve the plan"
---

## 1. Agree on the plan

- **You provide:** the request.
- **Agent does:** writes the plan.
- **You decide:** approve or redirect.
- **Output:** an agreed plan.

---

## 2. Build and verify

- **Agent does:** implements and runs gates.
- **You do:** watch at key moments.
- **Output:** a green implementation.
"""


def _run(journey_dir: pathlib.Path) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "LJC_JOURNEY_DIR": str(journey_dir)}
    return subprocess.run(
        [sys.executable, str(_SCRIPT)],
        capture_output=True, text=True, env=env, check=False,
    )


def _assert(condition: bool, msg: str) -> None:
    if not condition:
        print(f"FAIL: {msg}", file=sys.stderr)
        sys.exit(1)


def _write(d: pathlib.Path, name: str, content: str) -> None:
    (d / name).write_text(content, encoding="utf-8")


def test_valid_passes() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        j = pathlib.Path(tmp)
        _write(j, "alpha.md", _VALID)
        r = _run(j)
        _assert(r.returncode == 0, f"expected exit 0 for valid journey; got {r.returncode}\n{r.stderr}")


def test_missing_contract_key() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        j = pathlib.Path(tmp)
        _write(j, "alpha.md", _VALID.replace('  youReceive: "an artifact"\n', ""))
        r = _run(j)
        _assert(r.returncode == 1, f"expected exit 1 when a contract key is missing; got {r.returncode}")
        _assert("youReceive" in r.stderr, f"expected missing-key message; got:\n{r.stderr}")


def test_stage_missing_output() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        j = pathlib.Path(tmp)
        _write(j, "alpha.md", _VALID.replace("- **Output:** an agreed plan.\n", ""))
        r = _run(j)
        _assert(r.returncode == 1, f"expected exit 1 when a stage lacks Output; got {r.returncode}")
        _assert("Output" in r.stderr, f"expected missing-Output message; got:\n{r.stderr}")


def test_unknown_actor() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        j = pathlib.Path(tmp)
        _write(j, "alpha.md", _VALID.replace("- **Agent does:** writes the plan.", "- **Team does:** writes the plan."))
        r = _run(j)
        _assert(r.returncode == 1, f"expected exit 1 for an unknown actor token; got {r.returncode}")
        _assert("Team" in r.stderr, f"expected unknown-actor message; got:\n{r.stderr}")


def test_surviving_old_heading() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        j = pathlib.Path(tmp)
        _write(j, "alpha.md", _VALID.replace("## 2. Build and verify", "## Stage 2 — Build and verify"))
        r = _run(j)
        _assert(r.returncode == 1, f"expected exit 1 for a surviving `## Stage N —` heading; got {r.returncode}")
        _assert("old-format" in r.stderr.lower(), f"expected old-format message; got:\n{r.stderr}")


def main() -> None:
    tests = [
        test_valid_passes,
        test_missing_contract_key,
        test_stage_missing_output,
        test_unknown_actor,
        test_surviving_old_heading,
    ]
    for t in tests:
        t()
        print(f"  ok: {t.__name__}")
    print(f"test-lint-journey-contract: all {len(tests)} tests passed")


if __name__ == "__main__":
    main()
