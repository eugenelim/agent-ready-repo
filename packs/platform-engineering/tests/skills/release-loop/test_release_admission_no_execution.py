"""Reusable process/network prohibition seam and parity for every admission command."""

from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "release_engineering_release_loop_no_execution_helpers", HERE / "test_release_stage_check.py"
)
assert spec and spec.loader
stages = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = stages
spec.loader.exec_module(stages)
helpers = stages.helpers


def prohibit_execution(monkeypatch: pytest.MonkeyPatch) -> None:
    """Close common process and network seams for admission and collector suites."""
    helpers.prohibit_execution(monkeypatch)

    def refuse(*args: Any, **kwargs: Any) -> Any:
        """Fail if a script tries a direct operating-system process API."""
        raise AssertionError("external operation forbidden")

    for name in dir(os):
        if name.startswith(("exec", "spawn", "posix_spawn")) or name in ("fork", "forkpty", "popen"):
            monkeypatch.setattr(os, name, refuse)


@pytest.mark.parametrize("command", ["admit", "verify", "check-review", "check-stage", "repair-handoff"])
@pytest.mark.parametrize("valid", [False, True])
def test_command_parity(
    tmp_path: Path, capsys: Any, command: str, valid: bool,
) -> None:
    """Success and refusal results remain identical when external operations fail."""
    results = []
    for closed in (False, True):
        root = tmp_path / ("closed" if closed else "baseline")
        root.mkdir()
        with pytest.MonkeyPatch.context() as patch:
            if closed:
                prohibit_execution(patch)
            module = helpers.load_script("release_admission")
            stages.case.__wrapped__(root, module)
            admitted = json.loads((root / "admission.json").read_bytes())
            if command == "admit":
                args = ["admit", "release-handoff.yaml", "--policy", "trusted-policy.json",
                        "--expect-environment", "staging" if valid else "other", "--output", "new.json"]
            elif command == "verify":
                args = ["verify", "admission.json"]
                if not valid:
                    (root / "test-report.json").write_bytes(b"changed")
            elif command == "check-review":
                # Load the role fixture in a distinct root to avoid replacing an admission.
                review_root = root / "review"
                review_root.mkdir()
                _, record = stages.reviews.case.__wrapped__(
                    SimpleNamespace(param="reliability"), review_root, module
                )
                root = review_root
                (root / "review.json").write_text(json.dumps(record))
                rubric = helpers.PACK / ".apm/skills/release-loop/references/reliability-review.md"
                (root / "rubric.md").write_bytes(rubric.read_bytes())
                args = ["check-review", "review.json", "--admission", "admission.json", "--rubric", "rubric.md"]
                if not valid:
                    (root / "review.json").write_text("{}")
            elif command == "check-stage":
                args = ["check-stage", "--stage", "admission", "--admission", "admission.json"]
                if not valid:
                    (root / "test-report.json").write_bytes(b"changed")
            else:
                data = b"health check failed"
                (root / "failure.log").write_bytes(data)
                (root / "failure.json").write_text(json.dumps({
                    "candidate_sha256": admitted["candidate"]["sha256"],
                    "target": admitted["target"], "stage": "post-deploy",
                    "check": {"id": "health", "status": "fail" if valid else "pass"},
                    "observed_at": helpers.NOW,
                    "evidence": [{"id": "runtime", "path": "failure.log", "sha256": helpers.digest(data)}],
                }))
                args = ["repair-handoff", "--admission", "admission.json", "--failure", "failure.json"]
            results.append(helpers.invoke(module, root, capsys, *args))
    assert results[0] == results[1]
    assert results[0][0] == (0 if valid else 1)
