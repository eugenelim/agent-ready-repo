"""Derive § Grounding's five-path-state Tier-classifier claim."""

from __future__ import annotations

import sys

from _common import REPO_ROOT, fail
from agentbundle.catalogue_tooling.file_safety import sha256_confined_regular_file


def _state(path: str, entry: dict[str, str]) -> object:
    from agentbundle.config import PackState, State

    return State(packs={("probe", "claude-code"): PackState("1", files={path: entry})})


def main() -> int:
    try:
        from agentbundle.safety import Tier, classify

        path = "AGENTS.md"
        digest = sha256_confined_regular_file(REPO_ROOT, REPO_ROOT / path)
        cases = {
            "unrecorded": ("missing.txt", _state(path, {"sha": digest}), Tier.TIER_3),
            "absent": ("missing.txt", _state("missing.txt", {"sha": digest}), Tier.TIER_1),
            "matching": (path, _state(path, {"sha": digest}), Tier.TIER_1),
            "changed": (path, _state(path, {"sha": "0" * 64}), Tier.TIER_2),
            "present_null_sha": (path, _state(path, {}), Tier.TIER_2),
        }
        observed = {
            name: classify(candidate, REPO_ROOT, state).value
            for name, (candidate, state, _) in cases.items()
        }
        wrong = [
            name
            for name, (_, _, expected) in cases.items()
            if observed[name] != expected.value
        ]
        if wrong:
            return fail("Tier classifier differs for " + ", ".join(wrong))
        print(
            "Tier verdicts: "
            + ", ".join(f"{name}={value}" for name, value in observed.items())
        )
        print("residual: none")
        return 0
    except Exception as exc:  # pragma: no cover - one-line probe boundary
        return fail(f"tier derivation failed: {exc}")


if __name__ == "__main__":
    sys.exit(main())
