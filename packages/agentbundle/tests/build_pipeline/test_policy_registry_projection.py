"""The policy registry reaches both adapters and still selects correctly there."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

from agentbundle.build.adapters import ADAPTERS
from agentbundle.build.contract import load as load_contract
from agentbundle.build.main import CONTRACT_PATH

ROOT = Path(__file__).resolve().parents[4]
CORE_PACK = ROOT / "packs/core"
SELECTOR = CORE_PACK / ".apm/skills/work-loop/scripts/select-policy-families.py"

RELATIVE = "skills/work-loop/references/policy-families.md"
EXPECTED_LANDINGS = {
    "claude-code": f".claude/{RELATIVE}",
    "codex": f".agents/{RELATIVE}",
}
# AC9's comparison value. A literal, not the other projection: the two copies are
# byte-identical by construction, so comparing them to each other passes on an
# empty or wrong registry.
EXPECTED_IDS = ["the-razor", "cognitive-load"]


def test_policy_registry_projects_and_still_selects_on_both_adapters() -> None:
    """Each adapter lands the registry at its own path and selects from it.

    `--root` stays the repository while `--registry` moves to the projected
    copy. They are necessarily different trees: an adapter projection carries the
    skill, while seeds reach a consumer through the separate `scaffold` command,
    and every family `CODE-IMPLEMENTATION` selects is a `seed:` locator.
    """
    if not CORE_PACK.is_dir():
        # Return rather than skip. This tree is published: the export-boundary
        # gate builds an sdist and runs these tests inside it, where the engine
        # ships without the catalogue corpus it projects. That gate also polices
        # skip reasons — `check-artifact-contents.py` forbids any reason naming
        # `packs`, so a corpus-missing skip cannot hide a genuinely broken test.
        return
    contract = load_contract(CONTRACT_PATH)
    covered: set[str] = set()
    for adapter, own in EXPECTED_LANDINGS.items():
        other = next(v for k, v in EXPECTED_LANDINGS.items() if k != adapter)
        with tempfile.TemporaryDirectory() as raw:
            output = Path(raw)
            ADAPTERS[adapter](CORE_PACK, contract, output)

            landed = output / own
            assert landed.is_file(), f"{adapter} did not emit {own}"
            assert not (output / other).exists(), (
                f"{adapter} emitted {other}, which belongs to the other adapter"
            )

            proc = subprocess.run(
                [sys.executable, str(SELECTOR), "--registry", str(landed),
                 "--root", str(ROOT), "CODE-IMPLEMENTATION"],
                capture_output=True, text=True, check=False,
            )
            assert proc.returncode == 0, f"{adapter}: {proc.stderr}"
            emitted = [f["id"] for f in json.loads(proc.stdout)["families"]]
            assert emitted == EXPECTED_IDS, f"{adapter} selected {emitted}"
            covered.add(adapter)

    # Against a literal, not against the loop it just ran. Every assertion above
    # derives from the loop variable, so narrowing the loop to one adapter would
    # leave them all green while half the contract went unchecked.
    assert covered == {"claude-code", "codex"}, f"only exercised {sorted(covered)}"
