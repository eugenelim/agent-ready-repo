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
# The enquiry protocol is disclosed progressively: SKILL.md routes to the
# reference, which carries the CQ-REVIEW query. Assert both halves so an
# extraction that orphans the reference still fails here.
REVIEW_ENQUIRY_REFERENCE = (
    WORK_LOOP_SKILL.parent / "references" / "review-planning-enquiry.md"
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
    # Match the Markdown link, not the bare path: a plain-text mention of the
    # filename would satisfy a substring check while the route is broken.
    assert re.search(
        r"\]\(references/review-planning-enquiry\.md\)",
        WORK_LOOP_SKILL.read_text(encoding="utf-8"),
    ), "SKILL.md no longer links the review-planning enquiry reference"
    match = re.search(
        r'^\{"task_summary":"work-loop review:.*\}$',
        REVIEW_ENQUIRY_REFERENCE.read_text(encoding="utf-8"),
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
