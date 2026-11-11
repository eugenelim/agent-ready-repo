"""Roster coverage for the drain's pre-execution re-check (§ D6 re-run).

Spec: ``docs/specs/work-item-promotion-handoff`` — task T4. Before the
envelope executes a stored command, the drain re-runs the write path's own
stored-command validator over it — the same function, asserted by identity —
so a rule added upstream reaches this check with no edit here. Every row of
the capture spec's § D6 case table drives the re-check.
"""

from __future__ import annotations

import copy
import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = (
    REPO_ROOT / "packs" / "core" / ".apm" / "skills" / "project-knowledge" / "scripts"
)
CAPTURE_SPEC = REPO_ROOT / "docs" / "specs" / "work-item-capture" / "spec.md"


def _load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


DRAIN = _load_module("_roster_promotion_drain_recheck", SCRIPTS_DIR / "promotion_drain.py")
KS = DRAIN.KS


def _d6_cases() -> list[tuple[Any, str | None]]:
    """Every row of the capture spec's § D6 case table, parsed live: each
    row's argv and its expected catalog code (None for an admitted row)."""
    text = CAPTURE_SPEC.read_text(encoding="utf-8")
    section = re.search(r"^### D6 cases$(.*?)^(?=## )", text, re.MULTILINE | re.DOTALL)
    assert section is not None
    cases: list[tuple[Any, str | None]] = []
    for line in section.group(1).splitlines():
        if not line.startswith("| `"):
            continue
        cells = line.strip().strip("|").split("|")
        argv = json.loads(cells[0].strip().strip("`"))
        verdict = cells[1].strip()
        cases.append((argv, None if verdict == "**admit**" else verdict.strip("`")))
    return cases


def test_recheck_calls_the_write_path_validator_itself(
    monkeypatch: Any,
) -> None:
    calls: list[Any] = []

    def spy(value: Any) -> None:
        calls.append(copy.deepcopy(value))
        raise KS.PK.VerificationRouteRefusal("work_item_command_tool")

    monkeypatch.setattr(KS.PK, "_validate_verification_route", spy)
    result = DRAIN.rerun_command_recheck(
        {"command": ["cat", "x.txt"], "path": "x.txt"}
    )
    assert calls == [{"command": ["cat", "x.txt"], "path": "x.txt"}]
    assert result == {"verdict": "refused", "reason_code": "work_item_command_tool"}


def test_every_d6_case_row_drives_the_recheck() -> None:
    cases = _d6_cases()
    # The capture spec states the table carries 46 rows so a dropped row is
    # detectable; rows added upstream must drive this check unchanged.
    assert len(cases) >= 46
    for argv, expected_code in cases:
        result = DRAIN.rerun_command_recheck({"command": argv, "path": "docs/x.md"})
        if expected_code is None:
            assert result == {"verdict": "pass"}, argv
        else:
            assert result == {"verdict": "refused", "reason_code": expected_code}, argv


def test_string_command_and_bash_argv_are_each_refused() -> None:
    string_command = DRAIN.rerun_command_recheck(
        {"command": "cat src/a.py", "path": "docs/x.md"}
    )
    assert string_command == {
        "verdict": "refused",
        "reason_code": "work_item_command_shape",
    }
    bash = DRAIN.rerun_command_recheck(
        {"command": ["bash", "-c", "printf pwned"], "path": "docs/x.md"}
    )
    assert bash["verdict"] == "refused"
