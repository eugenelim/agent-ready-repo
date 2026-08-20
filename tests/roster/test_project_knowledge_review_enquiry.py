"""Repository-level roster check for review enquiry and its public parser."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

CATALOGUE_ROOT = Path(__file__).resolve().parents[2]
WORK_LOOP_SKILL = (
    CATALOGUE_ROOT / "packs" / "core" / ".apm" / "skills" / "work-loop" / "SKILL.md"
)
PROJECT_KNOWLEDGE = (
    CATALOGUE_ROOT
    / "packs"
    / "core"
    / ".apm"
    / "skills"
    / "project-knowledge"
    / "scripts"
    / "project_knowledge.py"
)


def test_documented_review_query_reaches_the_public_parser() -> None:
    match = re.search(
        r'^\{"task_summary":"work-loop review:.*\}$',
        WORK_LOOP_SKILL.read_text(encoding="utf-8"),
        re.MULTILINE,
    )
    assert match is not None
    query = json.loads(match.group(0))
    query["task_summary"] = "work-loop review: review integration contract"
    query["scope"] = "packs"

    result = subprocess.run(
        [
            sys.executable,
            str(PROJECT_KNOWLEDGE),
            "--enquire",
            "--repo-root",
            str(CATALOGUE_ROOT),
        ],
        input=json.dumps(query),
        capture_output=True,
        text=True,
        check=False,
    )

    diagnostic_or_result = result.stdout or result.stderr
    assert diagnostic_or_result, "public enquiry returned no result or diagnostic"
    payload = json.loads(diagnostic_or_result.splitlines()[-1])
    assert payload.get("reason_code") != "strict_parse"
