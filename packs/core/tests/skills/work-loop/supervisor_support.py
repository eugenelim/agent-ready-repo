"""Shared fixtures for the work-loop execution supervisor suites.

Loads the supervisor modules by path under unique names, and builds the
synthetic spec, plan, and cited ADR the suites edit.
"""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path
from types import ModuleType

import pytest

SCRIPTS = Path(__file__).resolve().parents[3] / ".apm" / "skills" / "work-loop" / "scripts"
PYTHON = sys.executable.replace("\\", "/")

# Suites that drive whole git-backed runs. They take minutes, so they run in
# their own CI lane, which sets this variable, rather than in the pack lane.
INTEGRATION = pytest.mark.skipif(
    os.environ.get("WORK_SUPERVISOR_INTEGRATION") != "1",
    reason="supervisor integration suite: runs in the supervisor integration lane "
    "(set WORK_SUPERVISOR_INTEGRATION=1)",
)


# Each script by literal path, so every file a suite loads stays visibly inside
# this pack.
_SCRIPT_PATHS = {
    "work-supervisor.py": SCRIPTS / "work-supervisor.py",
    "_supervisor_projector.py": SCRIPTS / "_supervisor_projector.py",
    "_policy_import.py": SCRIPTS / "_policy_import.py",
    "_security_capability.py": SCRIPTS / "_security_capability.py",
}


def load(filename: str) -> ModuleType:
    """Load a work-loop script by path under a pack- and skill-unique name."""
    alias = "core_work_loop_supervisor_" + filename.removesuffix(".py").replace("-", "_").lstrip(
        "_"
    )
    spec = importlib.util.spec_from_file_location(alias, str(_SCRIPT_PATHS[filename]))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[alias] = module
    spec.loader.exec_module(module)
    return module


SPEC = """# Spec: Calculator

- **Status:** Approved <!-- Draft | Approved | Implementing | Shipped | Archived -->
- **Owner:** Platform Core
- **Plan:** [`plan.md`](plan.md)
- **Constrained by:** ADR-0001
- **Contract:** `contracts/calc/`

## Outcome

Maintainers get a calculator that answers.

## What Changes

- `calc.py` arrives.

## Scope and Non-goals

Only the calculator; no user interface.

## Durable Outputs

| Semantic role | Destination |
| --- | --- |
| Release history | changelog |

## Agent Rules

### Never do

- Reach the network.

## Testing Strategy

- **Calculator (AC-0001):** TDD.

## Acceptance Criteria

- [ ] **AC-0001.** The calculator answers 42.
- [ ] **AC-0002.** The release note says ready.

## Follow-ons

none

## Terminal Intent

`code` — build the calculator.

## Accepted Risk

none

## Assumptions

none
"""

ADR = """# ADR-0001: Calculators answer

- **Status:** Accepted

## Context

Callers need an answer.

## Decision

The calculator answers 42.

## Consequences

None.
"""

STUB = "import calc\nassert calc.answer() == 42\n"


def stub_fence(
    path: str = "test_calc.py", body: str = STUB, red_exit: str = "1", indent: str = "    "
) -> str:
    """A stub fence as it sits inside a task's Tests: bullet."""
    lines = [f'{indent}```stub path={path} run="{PYTHON} {{path}}" red-exit={red_exit}']
    lines += [indent + line if line else "" for line in body.rstrip("\n").split("\n")]
    lines.append(f"{indent}```")
    return "\n".join(lines)


def task(
    number: str,
    title: str,
    *,
    depends: str = "none",
    touches: str = "`calc.py`",
    mode: str = "TDD",
    tests: str = "- **VI-1:** the calculator test passes.",
    done: str = "the test passes",
    effects: str | None = None,
    approach: str = "write it",
) -> str:
    lines = [
        f"### {number}: {title}",
        "",
        f"- **Depends on:** {depends}",
        f"- **Touches:** {touches}",
        f"- **Verification mode:** {mode}",
    ]
    if effects is not None:
        lines.append(f"- **Effects:** {effects}")
    lines += ["- **Tests:**", "  " + tests.replace("\n", "\n  ")]
    lines += [f"- **Done when:** {done}", f"- **Approach:** {approach}", ""]
    return "\n".join(lines)


TASKS = {
    "calc": lambda n="T1", **kw: task(
        n,
        "Calculator answers",
        tests="- **VI-1:** the calculator test.\n\n" + stub_fence(indent="  "),
        **kw,
    ),
    "push": lambda n="T2", **kw: task(
        n,
        "Release is pushed",
        depends=kw.pop("depends", "T1"),
        touches="`release.txt`",
        mode="goal-based",
        tests="no stub (goal-based)",
        done=kw.pop("done", "release.txt says ready"),
        effects=kw.pop("effects", "push"),
        **kw,
    ),
    "plain": lambda n="T3", **kw: task(
        n,
        "Plain note is written",
        touches="`plain.txt`",
        mode="goal-based",
        tests="no stub (goal-based)",
        done="plain.txt says done",
        **kw,
    ),
}


def plan(*tasks: str, header_effects: str | None = None) -> str:
    """A plan carrying *tasks* in order."""
    head = [
        "# Plan: Calculator",
        "",
        "- **Spec:** [`spec.md`](spec.md)",
        "- **Status:** Approved <!-- Drafting | Approved | Executing | Done -->",
    ]
    if header_effects is not None:
        head.append(f"- **Effects:** {header_effects}")
    head += ["", "## Approach", "", "Build it.", "", "## Tasks", ""]
    tail = ["## Changelog", "", "- 2026-10-13: plan approved by owner", ""]
    return "\n".join(head) + "\n" + "\n".join(tasks) + "\n" + "\n".join(tail)


PLAN = plan(TASKS["calc"](), TASKS["push"](), TASKS["plain"]())
