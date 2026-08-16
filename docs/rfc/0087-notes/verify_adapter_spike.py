"""Reproduce RFC-0087's nested-OKF adapter preservation spike."""

from __future__ import annotations

import hashlib
import importlib
import tempfile
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ADAPTERS = (
    "claude-code",
    "kiro-ide",
    "kiro-cli",
    "copilot",
    "cursor",
    "codex",
    "gemini",
)
MODULES = {
    "claude-code": "claude_code",
    "kiro-ide": "kiro_ide",
    "kiro-cli": "kiro_cli",
    "copilot": "copilot",
    "cursor": "cursor",
    "codex": "codex",
    "gemini": "gemini",
}
CONCEPT = b"""---
type: Playbook
title: Triage an AI cost anomaly
description: Decide whether a cost change is expected or actionable.
x-agentbundle:
  profile: agentbundle-okf/v1
  skill:
    name: triage-ai-cost-anomaly
x-foreign-system:
  preserved: true
---

## Procedure

Compare the observed unit cost with the reviewed baseline.
"""


def main() -> None:
    """Project one nested concept through each current adapter and compare bytes."""
    contract = tomllib.loads((ROOT / "contracts/adapter.toml").read_text())
    digest = hashlib.sha256(CONCEPT).hexdigest()
    with tempfile.TemporaryDirectory(prefix="okf-adapter-spike-") as raw:
        temporary_root = Path(raw)
        pack = temporary_root / "spike-pack"
        skill = pack / ".apm/skills/okf-router"
        concept = skill / "references/okf/playbooks/triage.md"
        concept.parent.mkdir(parents=True)
        (skill / "SKILL.md").write_text(
            "---\nname: okf-router\ndescription: Route OKF knowledge.\n---\n",
            encoding="utf-8",
        )
        concept.write_bytes(CONCEPT)

        for adapter in ADAPTERS:
            output = temporary_root / "out" / adapter
            module = importlib.import_module(
                f"agentbundle.build.adapters.{MODULES[adapter]}"
            )
            module.project(pack, contract, output)
            matches = list(output.rglob("triage.md"))
            if len(matches) != 1:
                raise AssertionError(
                    f"{adapter}: expected one triage.md, got {matches}"
                )
            if matches[0].read_bytes() != CONCEPT:
                raise AssertionError(f"{adapter}: projected bytes differ")
            relative_output = matches[0].relative_to(output)
            print(f"PASS {adapter} sha256:{digest} {relative_output}")


if __name__ == "__main__":
    main()
