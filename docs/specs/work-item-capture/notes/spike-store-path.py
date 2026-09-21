"""Spike 2: attempt a real work-item capture and record what actually refuses.

Settles three claims the previous grounding got wrong by reading:
  F7  does the partition validator allowlist the kind directory?
  F2  which literal sets genuinely pin the CAPTURE kind?
  F1  which reason codes can the writer actually emit?

Runs against a scratch copy of the store. Touches no tracked file.
"""
import importlib.util
import shutil
import sys
import tempfile
from pathlib import Path

REPO = Path("/Users/eu.gene.lim/orca/workspaces/agent-ready-repo/follow-ons-mgmt")
SCRIPTS = REPO / "packs/core/.apm/skills/project-knowledge/scripts"
sys.path.insert(0, str(SCRIPTS))


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


PK = load("project_knowledge")
KS = load("knowledge_store")


def work_item_request(kind="work-item"):
    body = b"placeholder"
    return {
        "contract_version": PK.CONTRACT_VERSION,
        "lesson": "a work item statement",
        "kind": kind,
        "project_scope": {
            "paths": ["docs/specs/work-item-capture/spec.md"],
            "audience": "project",
        },
        "competency_facets": ["CQ-CHANGE"],
        "destination_hint": {"type": "topic", "path": "docs/knowledge/observations"},
        "producer": {"workflow": "work-loop", "workflow_version": "1"},
        "semantic_gate": {
            "name": "capture-learnings",
            "artifact": "docs/specs/work-item-capture/spec.md",
        },
        "provenance": {"sources": [{"path": "docs/specs/work-item-capture/spec.md"}]},
        "freshness_anchor": {"path": "docs/specs/work-item-capture/spec.md",
                             "digest": PK.digest_bytes(body)},
        "observed_at": "2026-09-20T00:00:00Z",
        "privacy_attestation": {"reduced" if False else "reviewed": True,
                                "contains_private_data": False,
                                "contains_secrets": False,
                                "contains_instructions": False},
    }


def attempt(label, req, root):
    try:
        r = KS.capture_observation(root, req)
        return label, "WROTE", r.get("capture_id", "")[:12]
    except Exception as e:
        d = getattr(e, "diagnostic", None)
        code = d.get("reason_code") if isinstance(d, dict) else None
        return label, type(e).__name__, code or str(e)[:60]


import subprocess as _sp  # noqa: E402  (deliberate: runs after the tree probe above)

with tempfile.TemporaryDirectory() as tmp:
    # resolve_worktree_root shells out to `git rev-parse --show-toplevel`, and
    # _assert_confined_components refuses a symlinked component — so the scratch
    # tree must be a real git repo at a fully resolved path. A bare .git dir is
    # not enough; the first harness got `confinement` on the CONTROL for this
    # reason, which is why its end-to-end result proved nothing.
    root = Path(tmp).resolve() / "repo"
    shutil.copytree(REPO / "docs/knowledge", root / "docs/knowledge")
    _sp.run(["git", "init", "-q", str(root)], check=True, capture_output=True)

    rows = []
    rows.append(attempt(
        "control: kind=gotcha (existing vocabulary)", work_item_request("gotcha"), root
    ))
    rows.append(attempt(
        "target:  kind=work-item (unwidened tree)", work_item_request("work-item"), root
    ))

    print("=== Q1/Q3: what refuses a work-item capture today, and with which code? ===")
    for lbl, outcome, detail in rows:
        print(f"  {lbl:<44} {outcome:<20} {detail}")

    print("\n=== Q1: is the refusal the partition validator? ===")
    for part in ["observations/gotcha/2026-09.jsonl", "observations/work-item/2026-09.jsonl"]:
        try:
            KS._validate_partition_name(part)
            v = "accepted"
        except Exception as e:
            d = getattr(e, "diagnostic", None)
            v = f"REFUSED ({d.get('reason_code') if isinstance(d, dict) else e})"
        print(f"  _validate_partition_name({part!r}) -> {v}")

print("\n=== Q2: which literal sets pin the CAPTURE kind vs another vocabulary? ===")
src_ks = (SCRIPTS / "knowledge_store.py").read_text().splitlines()
src_pk = (SCRIPTS / "project_knowledge.py").read_text().splitlines()
lint = (
    REPO / "packs/core/.apm/skills/work-loop/scripts/lint-knowledge.py"
).read_text(encoding="utf-8").splitlines()
for label, lines in (
    ("knowledge_store.py", src_ks),
    ("project_knowledge.py", src_pk),
    ("lint-knowledge.py", lint),
):
    for i, line in enumerate(lines, 1):
        if "antipattern" in line and ("{" in line or "(" in line):
            ctx = " / ".join(x.strip() for x in lines[max(0, i - 3):i - 1] if x.strip())[:88]
            print(f"  {label}:{i}\n      {line.strip()[:96]}\n      context: {ctx}")

print("\n=== Q3: the closed catalog the writer may emit ===")
print(" ", ", ".join(PK.REQUIRED_DIAGNOSTIC_CODES))
