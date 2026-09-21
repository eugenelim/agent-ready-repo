"""The worked example in the work-loop capture reference must still work.

Two agents driving the close from that reference alone both failed with
`strict_parse` because the reference named the two commands and not the
request they read. The example closed that gap, so it is load-bearing
documentation: if it stops producing a capture, the reference is wrong
again and nothing else in the suite notices.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

from knowledge_test_support import (
    initialize_empty_v1_repo,
    load_knowledge_store_module,
    load_project_knowledge_module,
)

_PACK = Path(__file__).resolve().parents[3]
_REFERENCE = _PACK / ".apm" / "skills" / "work-loop" / "references" / (
    "work-item-capture.md"
)
_SCRIPT = _PACK / ".apm" / "skills" / "project-knowledge" / "scripts" / (
    "project_knowledge.py"
)


def _documented_example() -> dict[str, object]:
    blocks = re.findall(r"```json\n(.*?)\n```", _REFERENCE.read_text(), re.S)
    assert len(blocks) == 1, (
        f"expected exactly one JSON example in {_REFERENCE.name}, found "
        f"{len(blocks)} — this test reads the example by position"
    )
    return json.loads(blocks[0])


def _run(argv: list[str], stdin: bytes) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        [sys.executable, str(_SCRIPT), *argv], input=stdin,
        capture_output=True, timeout=120,
    )


def test_the_referenced_example_still_produces_a_capture(tmp_path: Path) -> None:
    store = load_knowledge_store_module()
    repo = initialize_empty_v1_repo(tmp_path, store)
    request = _documented_example()

    # The example's freshness anchor names this store's index, whose digest
    # is per-store. Everything else is used exactly as documented -- a
    # rewrite here would test the fixture instead of the document.
    raw = (repo / "docs" / "knowledge" / "topics.index.json").read_bytes()
    request["freshness_anchor"] = {
        "path": "docs/knowledge/topics.index.json",
        "digest": {
            "kind": "sha256-bytes-v1",
            "sha256": hashlib.sha256(raw).hexdigest(),
            "byte_length": len(raw),
        },
    }
    payload = json.dumps(request).encode()

    prepared = _run(
        ["--reasoning-payload", "--repo-root", str(repo), "--declined-ordinal", "0"],
        payload,
    )
    assert prepared.returncode == 0, prepared.stdout + prepared.stderr
    key = json.loads(prepared.stdout)["correlation_key"]

    admitted = _run(
        ["--capture", "--repo-root", str(repo),
         "--writer-time", "2026-09-21T11:00:00Z",
         "--reasoning-verdict", "admit",
         "--reasoning-correlation-key", key,
         "--declined-ordinal", "0"],
        payload,
    )
    assert admitted.returncode == 0, admitted.stdout + admitted.stderr
    assert json.loads(admitted.stdout)["partition"].startswith("observations/work-item/")


def test_the_reference_names_both_commands_it_documents() -> None:
    """The example is only usable with the two flags beside it."""

    text = _REFERENCE.read_text()
    for flag in ("--reasoning-payload", "--reasoning-correlation-key",
                 "--reasoning-verdict", "--declined-ordinal"):
        assert flag in text, f"{_REFERENCE.name} no longer names {flag}"


def test_the_reference_names_every_required_work_item_key() -> None:
    """Derived from the validator's own tuples, not a second hand-written
    list. Two QA agents failed with `strict_parse` because the reference
    described the fields in prose without naming their JSON keys; a key
    added to the contract without being documented reds here.
    """

    module = load_project_knowledge_module()
    text = _REFERENCE.read_text()
    required = list(module.WORK_ITEM_BASE_REQUIRED_FIELDS)
    for shape_fields in module.WORK_ITEM_SHAPE_REQUIRED_FIELDS.values():
        required.extend(shape_fields)
    # `defect` declares no extra required field in the validator, but the
    # reference must still name the pair it asks for in prose.
    required.extend(["observed", "intended"])
    undocumented = sorted({f for f in required if f"`{f}`" not in text})
    assert not undocumented, (
        f"{_REFERENCE.name} does not name these required keys: {undocumented}"
    )
    for shape in module.WORK_ITEM_SHAPES:
        assert f"`{shape}`" in text, f"{_REFERENCE.name} does not name shape {shape}"
