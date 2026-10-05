#!/usr/bin/env python3
"""Focused construction tests for the pack JavaScript workflow."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from selftest_harness import run_cases

BOUNDARY_PATH = (
    Path(__file__).resolve().parents[1]
    / "tools"
    / "lint-pack-test-boundary.py"
)


def _load_boundary():
    # NOT `selftest_harness.load`: that helper never registers the module in
    # `sys.modules`, and `lint-pack-test-boundary.py` declares a frozen
    # dataclass at import time, which CPython resolves through
    # `sys.modules[cls.__module__]`. The shared loader therefore raises
    # `AttributeError: 'NoneType' object has no attribute '__dict__'` on this
    # subject. The registration line below is the whole difference.
    spec = importlib.util.spec_from_file_location("pack_js_boundary", BOUNDARY_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


BOUNDARY = _load_boundary()


# STUB: AC-0010
def test_node_runner_inherits_pack_test_working_directory() -> None:
    workflow = """
steps:
  - name: renderer suite
    working-directory: packs/converters/tests/skills/render-proof
    run: node renderer.test.js
"""
    runners = BOUNDARY._workflow_runner_lines("pack-javascript.yml", workflow)

    assert any(
        "packs/converters/tests/skills/render-proof" in runner.tokens
        for runner in runners
    )


if __name__ == "__main__":
    raise SystemExit(run_cases(globals(), "pack-javascript-workflow"))
