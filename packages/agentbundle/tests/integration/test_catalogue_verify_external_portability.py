"""End-to-end portability proof for an external catalogue."""

import json
import os
import subprocess
import sys
from pathlib import Path

from agentbundle.catalogue_tooling.verify import _VERIFY_STEPS

FIXTURE = Path(__file__).parents[1] / "fixtures" / "external_catalogue"


def _run_verify() -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    package_root = str(Path(__file__).parents[2])
    env["PYTHONPATH"] = os.pathsep.join(
        [package_root, *filter(None, env.get("PYTHONPATH", "").split(os.pathsep))]
    )
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "agentbundle",
            "catalogue",
            "verify",
            "--root",
            str(FIXTURE),
            "--format",
            "json",
        ],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )


def test_clean_external_catalogue_verifies():
    result = _run_verify()
    assert result.returncode == 0, result.stderr + result.stdout
    payload = json.loads(result.stdout[result.stdout.index("{") :])
    assert payload["ok"] is True
    assert payload["diagnostics"] == []


def test_portable_seed_does_not_create_host_specific_finding():
    result = _run_verify()
    payload = json.loads(result.stdout[result.stdout.index("{") :])
    assert not any(
        "agent-ready-repo" in item["message"] for item in payload["diagnostics"]
    )


def test_pipeline_has_nineteen_steps():
    assert len(_VERIFY_STEPS) == 19
